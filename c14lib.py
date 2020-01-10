import numpy as np
import multiprocessing as mp
from collections import defaultdict
from scipy.interpolate import interp1d

def load_calibration_curve(fcalib):
	# load calibration curve
	# data from: fcalib 14c file
	# returns: [[CalBP, ConvBP, CalSigma], ...], sorted by CalBP
	
	with open(fcalib, "r") as f:
		data = f.read()
	data = data.split("\n")
	cal_curve = []
	for line in data:
		if line.startswith("#"):
			continue
		cal_curve.append([float(value) for value in line.split(",")])
	cal_curve = np.array(cal_curve)
	cal_curve = cal_curve[np.argsort(cal_curve[:,0])]
	
	return cal_curve

def calibrate(c14age, uncert, curve_conv_age, curve_uncert):
	# calibrate a 14C measurement
	# calibration formula as defined by Bronk Ramsey 2008, doi: 10.1111/j.1475-4754.2008.00394.x
	# c14age: uncalibrated 14C age BP
	# uncert: 1 sigma uncertainty
	
	sigma_sum = uncert**2 + curve_uncert**2
	return (np.exp(-(c14age - curve_conv_age)**2 / (2 * sigma_sum)) / np.sqrt(sigma_sum))

def get_range(c14age, uncert, curve, cal_BP):
	# returns range, distribution
	# range = interval length of calibrated age range at 95.4% probability level in years BP
	# distribution = probability distribution of calibrated 14C date on the calibration curve
	
	dist = calibrate(c14age, uncert, curve[:,1], curve[:,2])
	dist = interp1d(curve[:,0], dist)(cal_BP)
	dist = dist / dist.sum()
	idxs = np.argsort(dist)[::-1]
	dist_sum = np.cumsum(dist[idxs])
	cal_BP = cal_BP[idxs][dist_sum <= 0.954]
	return cal_BP.max() - cal_BP.min(), dist

def calc_precentile(rng, Ps, k):
	# rngs = [range, ...]
	# Ps = [P, ...]; in order of rngs; probabilities of the particular ranges
	# k = percentile value (0..1)
	
	rng = rng.copy()
	Ps = Ps.copy()
	
	Ps = Ps[np.argsort(rng)]
	rng.sort()
	
	Ps_sum = np.cumsum(Ps)
	k_norm = k * Ps_sum[-1]
	idx = np.argmin(np.abs(Ps_sum - k_norm))
	if Ps_sum[idx] < k_norm:
		idx += 1
	return rng[idx]

def calc_ranges_worker(c14ages, uncert, curve, cal_BP, results):
	
	while True:
		try:
			c14age = c14ages.pop()
		except:
			break
		rng, dist = get_range(c14age, uncert, curve, cal_BP)
		results.append([dist, rng])

def calc_ranges(cal_BP_from, cal_BP_to, uncert, curve_path, view):
	
	curve = load_calibration_curve(curve_path) # [[CalBP, ConvBP, CalSigma], ...]
	
	c14_rng = curve[(curve[:,0] >= cal_BP_from) & (curve[:,0] <= cal_BP_to)][:,1]
	c14_from = int(round(c14_rng.min() - 2*uncert))
	c14_to = int(round(c14_rng.max() + 2*uncert))
	
	n_cpus = min(8, max(1, mp.cpu_count() - 1))
	manager = mp.Manager()
	c14ages = manager.list(range(c14_from, c14_to + 1))
	results = manager.list() # [[dist, rng], ...]
	
	view.set_status("Calculating ranges (%d CPUs used)" % (n_cpus))
	
	cal_BP = np.arange(curve[:,0].min(), curve[:,0].max(), 0.5)
	
	procs = []
	for pi in range(n_cpus):
		procs.append(mp.Process(target = calc_ranges_worker, args = (c14ages, uncert, curve, cal_BP, results)))
		procs[-1].start()
	for proc in procs:
		proc.join()
	for proc in procs:
		proc.terminate()
		proc = None
	
	cal_BP_idxs = np.where((cal_BP >= cal_BP_from) & (cal_BP <= cal_BP_to))[0]
	
	view.set_status("Collecting data")
	
	collect = defaultdict(list) #  {year BP: [[rng, p], ...], ...}
	cmax = len(results)
	cnt = 1
	for dist, rng in results:
		view.update_progress(int(round((cnt/cmax)*100)))
		cnt += 1
		for idx in cal_BP_idxs:
			collect[cal_BP[idx]].append([rng, dist[idx]])
	
	view.set_status("Calculating means")
	
	res = []  # [[year BP, mean range, 5th percentile range, 95th percentile range], ...]
	for idx in cal_BP_idxs:
		year = cal_BP[idx]
		collect[year] = np.array(collect[year])
		m = (collect[year][:,0] * collect[year][:,1]).sum() / collect[year][:,1].sum()  # mean
		perc5 = calc_precentile(collect[year][:,0], collect[year][:,1], 0.05)
		perc95 = calc_precentile(collect[year][:,0], collect[year][:,1], 0.95)
		res.append([year, m, perc5, perc95])
	
	return np.array(res)
