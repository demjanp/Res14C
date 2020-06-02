from c14lib import calc_ranges
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib import pyplot
import os

def path_to_csv(path):
	
	path, name = os.path.split(os.path.abspath(path))
	if not name.lower().endswith(".csv"):
		if "." in name:
			name = name.split(".")[0]
		name = "%s.csv" % (name)
	return os.path.join(path, name)

def set_input(input, value):
	
	input.delete(0, tk.END)
	input.insert(0, value)

def check_numeric(entry):
	
	value = entry.get()
	if value.isdigit():
		return True
	return False

class MainApp(tk.Tk):
	
	def __init__(self):
		
		tk.Tk.__init__(self)
		
		self.title("Res14C")
		try:
			self.iconbitmap("res14c.ico")
		except tk.TclError as e:
			pass
		
		frame = tk.Frame(self)
		frame.pack(padx = 5, pady = 5)
		
		tk.Label(frame, text = "Calculate Radiocarbon Dating Resolution", font = ("Arial 10 bold")).grid(row = 0, column = 0, padx = 5, pady = 5, columnspan = 5)
		
		tk.Label(frame, text = "Time Range:").grid(row = 2, column = 0, padx = 2, pady = 2, sticky = tk.E)
		frame_from_to = tk.Frame(frame)
		frame_from_to.grid(row = 2, column = 1, padx = 2, pady = 2, sticky = tk.W)
		
		self.input_from = tk.Entry(frame_from_to, width = 10)
		self.input_from.pack(side = tk.LEFT)
		tk.Label(frame_from_to, text = " .. ").pack(side = tk.LEFT)
		self.input_to = tk.Entry(frame_from_to, width = 10)
		self.input_to.pack(side = tk.LEFT)
		tk.Label(frame_from_to, text = "Years BP").pack(side = tk.LEFT)
		
		tk.Label(frame, text = "Uncertainty:").grid(row = 3, column = 0, padx = 2, pady = 2, sticky = tk.E)
		frame_uncert = tk.Frame(frame)
		frame_uncert.grid(row = 3, column = 1, padx = 2, pady = 2, sticky = tk.W)
		self.input_uncert = tk.Entry(frame_uncert, width = 10)
		self.input_uncert.pack(side = tk.LEFT)
		tk.Label(frame_uncert, text = "14C Years").pack(side = tk.LEFT)
		
		tk.Label(frame, text = "Calibration Curve:").grid(row = 4, column = 0, padx = 2, pady = 2, sticky = tk.E)
		self.input_curve = tk.Entry(frame, width = 50)
		self.input_curve.grid(row = 4, column = 1, padx = 2, pady = 2, columnspan = 3, sticky = tk.W)
		self.btn_curve = tk.Button(frame, text = "Browse..", command = self.clicked_curve)
		self.btn_curve.grid(row = 4, column = 4, padx = 2, pady = 2, sticky = tk.W)
		
		tk.Label(frame, text = "Save Output As:").grid(row = 5, column = 0, padx = 2, pady = 2, sticky = tk.E)
		self.input_save_as = tk.Entry(frame, width = 50)
		self.input_save_as.grid(row = 5, column = 1, padx = 2, pady = 2, columnspan = 3, sticky = tk.W)
		self.btn_save_as = tk.Button(frame, text = "Browse..", command = self.clicked_save_as)
		self.btn_save_as.grid(row = 5, column = 4, padx = 2, pady = 2, sticky = tk.W)
		
		self.btn_calculate = tk.Button(frame, text = "Calculate", command = self.clicked_calculate)
		self.btn_calculate.grid(row = 6, column = 0, padx = 10, pady = 10, columnspan = 5)
		
		self.label_status = tk.Label(frame, text = "")
		self.label_status.grid(row = 7, column = 0, padx = 10, pady = 2, columnspan = 5)
		
		self.progress = ttk.Progressbar(frame, orient = tk.HORIZONTAL, length = 400, mode = "determinate")
		self.progress.grid(row = 8, column = 0, padx = 10, pady = 2, columnspan = 5)
		
		text_descr = tk.Text(self, height = 4, wrap = tk.WORD, padx = 5, pady = 5)
		text_descr.insert(tk.INSERT, '''Svetlik, I., A. J. T. Jull, M. Molnár, P. P. Povinec, T. Kolář, P. Demján, K. Pachnerova Brabcova, et al. “The Best Possible Time Resolution: How Precise Could a Radiocarbon Dating Method Be?” Radiocarbon 61, no. 6 (December 2019): 1729–40. https://doi.org/10.1017/RDC.2019.134.''')
		text_descr.pack(fill = "both", expand = True, padx = 5, pady = 5)
		
		set_input(self.input_from, "500")
		set_input(self.input_to, "5000")
		set_input(self.input_uncert, "20")
		set_input(self.input_curve, os.path.join(os.path.abspath("."), "intcal13.14c"))
		set_input(self.input_save_as, "output.csv")
	
	def update_progress(self, value):
		
		self.progress["value"] = value
		self.update_idletasks()
	
	def set_status(self, value):
		
		self.label_status["text"] = "               %s             " % (value)
		self.update_idletasks()
		
	def clicked_curve(self):
		
		file = filedialog.askopenfilename(initialdir = ".", filetypes = (("Text files","*.14c"),("all files","*.*")))
		set_input(self.input_curve, os.path.abspath(file))
		
	def clicked_save_as(self):
		
		file = filedialog.asksaveasfilename(initialdir = ".", filetypes = (("CSV (comma-separated values)","*.csv"),))
		if file:
			path = path_to_csv(file)
			set_input(self.input_save_as, path)
	
	def clicked_calculate(self):
		
		if (not check_numeric(self.input_from)) or (not check_numeric(self.input_to)):
			messagebox.showinfo("Input Missing", "Time range must be specified as an integer number of years BP")
			return
		if not check_numeric(self.input_uncert):
			messagebox.showinfo("Input Missing", "Dating uncertainty must be specified as an integer number of 14C years")
			return
		cal_BP_from = int(self.input_from.get())
		cal_BP_to = int(self.input_to.get())
		uncert = int(self.input_uncert.get())
		curve_path = self.input_curve.get()
		save_path = self.input_save_as.get()
		if curve_path:
			curve_path = os.path.abspath(curve_path)
		if not os.path.isfile(curve_path):
			messagebox.showinfo("Input Missing", "Valid path to a C14 calibration data file in the proper format must be provided.\nSee e.g. http://radiocarbon.webhost.uits.arizona.edu/node/19/intcal13.14c")
			return
		if save_path:
			save_path = path_to_csv(save_path)
			save_dir = os.path.split(save_path)[0]
			if not os.path.isdir(save_dir):
				save_path = ""
		if not save_path:
			messagebox.showinfo("Input Missing", "An output CSV file in an existing directory must be specified")
			return
		
		self.btn_calculate["state"] = tk.DISABLED
		
		res = calc_ranges(cal_BP_from, cal_BP_to, uncert, curve_path, self)
		# res = [[year BP, mean range, 5th percentile range, 95th percentile range], ...]
		
		text = "Resolution of radiocarbon dating\nAll values in Calendar Years BP\n"
		text += "Sample Age,Mean Resolution,5th Percentile Resolution,95th Percentile Resolution\n"
		for year, m, perc5, perc95 in res:
			text += "%f,%f,%f,%f\n" % (year, m, perc5, perc95)
		with open(save_path, "w") as f:
			f.write(text)
		
		messagebox.showinfo("Saved", "Results saved as: %s" % (save_path))
		
		self.set_status("")
		self.update_progress(0)
		
		self.btn_calculate["state"] = tk.NORMAL
		
		pyplot.title("Resolution of radiocarbon dating")
		pyplot.fill_between(1950 - res[:,0], res[:,2], res[:,3], color = "lightgrey", label = "90% confidence interval")
		pyplot.plot(1950 - res[:,0], res[:,1], color = "k", label = "Mean")
		pyplot.xlabel("Sampe Age (Calendar Years CE)")
		pyplot.ylabel("Dating Resolution (Calendar Years)")
		pyplot.xlim(1950 - cal_BP_to - 100, 1950 - cal_BP_from + 100)
		pyplot.legend()
		pyplot.tight_layout()
		pyplot.show()

