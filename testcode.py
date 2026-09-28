from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import cv2
import numpy as np

try:
	from PIL import Image, ImageTk
except ImportError:
	Image = None
	ImageTk = None


class ImageProcessingApp:
	def __init__(self, root):
		self.root = root
		self.root.title("Xử lý ảnh | OpenCV + Pillow")
		self.root.geometry("1180x820")
		self.root.minsize(850, 650)
		self.root.configure(bg="#f2f4f1")

		self.image_path = None
		self.second_path = None
		self.image = None
		self.second_image = None
		self.brightness_value = tk.IntVar(master=root, value=0)
		self.contrast_value = tk.IntVar(master=root, value=100)
		self.saturation_value = tk.IntVar(master=root, value=100)
		self.zoom_value = tk.DoubleVar(master=root, value=1.0)
		self.rotation_value = tk.IntVar(master=root, value=0)
		self.offset_x_value = tk.IntVar(master=root, value=0)
		self.offset_y_value = tk.IntVar(master=root, value=0)
		self.preview_labels = {}
		self.preview_details = {}
		self.preview_photos = {}

		style = ttk.Style()
		style.theme_use("clam")
		style.configure("TProgressbar", troughcolor="#e3e8e2", background="#25816b")

		self._build_ui()

	def _build_ui(self):
		header = tk.Frame(self.root, bg="#183e36", padx=26, pady=20)
		header.pack(fill="x")
		tk.Label(
			header,
			text="BÀN LÀM VIỆC HÌNH ẢNH",
			font=("Segoe UI", 10, "bold"),
			foreground="#a9d5c8",
			background="#183e36",
		).pack(anchor="w")
		tk.Label(
			header,
			text="OpenCV  /  Pillow",
			font=("Segoe UI", 23, "bold"),
			foreground="#ffffff",
			background="#183e36",
		).pack(anchor="w", pady=(3, 0))

		controls = tk.Frame(self.root, bg="#f2f4f1", padx=22, pady=14)
		controls.pack(fill="x")
		self._button(controls, "Chọn ảnh 1", self.choose_first, "#25816b").pack(side="left", padx=(0, 8))
		self._button(controls, "Chọn ảnh 2", self.choose_second, "#386b78").pack(side="left", padx=8)
		self._button(controls, "Phân tích ảnh", self.analyze, "#183e36").pack(side="left", padx=8)
		self._button(controls, "Đặt lại", self.reset, "#68766f").pack(side="left", padx=8)
		self._button(controls, "Lưu PNG / JPEG / BMP", self.save_formats, "#b15d3a").pack(side="right")

		self.files_text = tk.StringVar(value="Chưa chọn ảnh")
		file_bar = tk.Label(
			self.root,
			textvariable=self.files_text,
			anchor="w",
			bg="#e5ebe6",
			fg="#375149",
			font=("Segoe UI", 9),
			padx=24,
			pady=9,
		)
		file_bar.pack(fill="x", padx=22, pady=(0, 12))

		notebook = ttk.Notebook(self.root)
		notebook.pack(fill="both", expand=True, padx=16, pady=(0, 8))
		color_tab = tk.Frame(notebook, bg="#f2f4f1")
		brightness_tab = tk.Frame(notebook, bg="#f2f4f1")
		geometry_tab = tk.Frame(notebook, bg="#f2f4f1")
		notebook.add(color_tab, text="Ảnh và màu")
		notebook.add(brightness_tab, text="Độ sáng")
		notebook.add(geometry_tab, text="Hình học")

		self._create_gallery(
			color_tab,
			[
			("opencv", "ẢNH GỐC · OPENCV"),
			("pillow", "ẢNH ĐỌC BẰNG PILLOW"),
			("second", "ẢNH THỨ HAI"),
			("gray", "GRAYSCALE"),
			("hue", "H · HUE (MÀU GIẢ)"),
			("saturation", "S · SATURATION"),
			("value", "V · VALUE"),
			("and", "BITWISE AND"),
			],
			columns=4,
		)

		adjustment_controls = tk.Frame(brightness_tab, bg="#f2f4f1", padx=14, pady=8)
		adjustment_controls.pack(fill="x")
		self._add_adjustment_slider(
			adjustment_controls, "Sáng / tối", -100, 100, self.brightness_value, "-100 tối hơn · 0 gốc · +100 sáng hơn"
		)
		self._add_adjustment_slider(
			adjustment_controls, "Tương phản", 0, 200, self.contrast_value, "0% thấp · 100% gốc · 200% cao"
		)
		self._add_adjustment_slider(
			adjustment_controls, "Bão hòa màu", 0, 200, self.saturation_value, "0% không màu · 100% gốc · 200% cao"
		)
		self._create_gallery(
			brightness_tab,
			[
				("brightness_original", "ẢNH GỐC"),
				("bright", "ẢNH TĂNG SÁNG"),
			],
			columns=2,
		)
		geometry_controls = tk.Frame(geometry_tab, bg="#f2f4f1", padx=12, pady=4)
		geometry_controls.pack(fill="x")
		self._add_geometry_slider(geometry_controls, "Tỷ lệ", 0.5, 1.5, self.zoom_value, 0.1)
		self._add_geometry_slider(geometry_controls, "Xoay (độ)", 0, 360, self.rotation_value, 1)
		self._add_geometry_slider(geometry_controls, "Dịch ngang X (px)", -50, 50, self.offset_x_value, 1)
		self._add_geometry_slider(geometry_controls, "Dịch dọc Y (px)", -50, 50, self.offset_y_value, 1)
		self._create_gallery(
			geometry_tab,
			[
				("geometry_original", "ẢNH GỐC"),
				("rotate", "XOAY THEO GÓC ĐÃ CHỌN"),
				("translate", "DỊCH THEO X / Y ĐÃ CHỌN"),
				("zoom", "THU PHÓNG THEO TỶ LỆ ĐÃ CHỌN"),
			],
			columns=2,
		)

		self.status_text = tk.StringVar(value="Chọn ảnh để bắt đầu.")
		status = tk.Label(
			self.root,
			textvariable=self.status_text,
			anchor="w",
			bg="#183e36",
			fg="#ffffff",
			font=("Segoe UI", 9),
			padx=24,
			pady=10,
		)
		status.pack(fill="x", side="bottom")

	def _add_adjustment_slider(self, parent, label, start, end, variable, scale_hint):
		control = tk.Frame(parent, bg="#f2f4f1")
		control.pack(fill="x", pady=3)
		tk.Label(
			control,
			text=label,
			font=("Segoe UI", 9, "bold"),
			background="#f2f4f1",
			foreground="#375149",
			width=16,
			anchor="w",
		).pack(side="left")
		tk.Scale(
			control,
			from_=start,
			to=end,
			resolution=1,
			orient="horizontal",
			variable=variable,
			command=lambda value, adjustment=label: self._on_adjustment_change(adjustment, value),
			showvalue=True,
			bg="#f2f4f1",
			fg="#183e36",
			troughcolor="#dce4dd",
			highlightthickness=0,
			bd=0,
		).pack(side="left", fill="x", expand=True, padx=8)
		tk.Label(
			control,
			text=scale_hint,
			font=("Segoe UI", 8),
			background="#f2f4f1",
			foreground="#75847c",
			width=36,
			anchor="w",
		).pack(side="right")

	def _add_geometry_slider(self, parent, label, start, end, variable, resolution):
		control = tk.Frame(parent, bg="#f2f4f1")
		control.pack(side="left", fill="x", expand=True, padx=5)
		tk.Label(
			control,
			text=label,
			font=("Segoe UI", 9, "bold"),
			background="#f2f4f1",
			foreground="#375149",
		).pack(anchor="w")
		tk.Scale(
			control,
			from_=start,
			to=end,
			resolution=resolution,
			orient="horizontal",
			variable=variable,
			command=self._on_geometry_change,
			showvalue=True,
			bg="#f2f4f1",
			fg="#183e36",
			troughcolor="#dce4dd",
			highlightthickness=0,
			bd=0,
		).pack(fill="x")
		tk.Label(
			control,
			text=f"{start} đến {end} · bước {resolution}",
			font=("Segoe UI", 8),
			background="#f2f4f1",
			foreground="#75847c",
		).pack(anchor="w")

	def _create_gallery(self, parent, cards, columns):
		gallery = tk.Frame(parent, bg="#f2f4f1", padx=4, pady=2)
		gallery.pack(fill="both", expand=True)
		for index, (key, title) in enumerate(cards):
			card = tk.Frame(gallery, bg="#ffffff", highlightbackground="#dce4dd", highlightthickness=1)
			card.grid(row=index // columns, column=index % columns, sticky="nsew", padx=6, pady=6)
			gallery.grid_columnconfigure(index % columns, weight=1, uniform="preview")
			gallery.grid_rowconfigure(index // columns, weight=1, uniform="preview")
			ttk.Label(
				card,
				text=title,
				font=("Segoe UI", 9, "bold"),
				foreground="#42665a",
				background="#ffffff",
				padding=(12, 10),
			).pack(anchor="w")
			preview = tk.Label(
				card,
				text="Chưa có ảnh",
				font=("Segoe UI", 10),
				foreground="#89978f",
				background="#f5f7f5",
				width=34,
				height=9,
			)
			preview.pack(fill="both", expand=True, padx=10, pady=(0, 5))
			detail = tk.Label(
				card,
				text="",
				font=("Segoe UI", 8),
				foreground="#75847c",
				background="#ffffff",
				anchor="w",
				padx=12,
				pady=8,
			)
			detail.pack(fill="x")
			self.preview_labels[key] = preview
			self.preview_details[key] = detail

	def _button(self, parent, text, command, color):
		return tk.Button(
			parent,
			text=text,
			command=command,
			font=("Segoe UI", 9, "bold"),
			fg="#ffffff",
			bg=color,
			activeforeground="#ffffff",
			activebackground="#285d50",
			relief="flat",
			padx=14,
			pady=9,
			cursor="hand2",
		)

	def _choose_image(self, image_number):
		path = filedialog.askopenfilename(
			title=f"Chọn ảnh {image_number}",
			filetypes=[("Tệp ảnh", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"), ("Tất cả tệp", "*.*")],
		)
		if not path:
			return

		image = cv2.imread(path, cv2.IMREAD_COLOR)
		if image is None:
			messagebox.showerror("Không đọc được ảnh", f"OpenCV không thể đọc tệp:\n{path}")
			return

		if image_number == 1:
			self.image_path = Path(path)
			self.image = image
			self._clear_processed_previews()
			self._show_array("opencv", cv2.cvtColor(image, cv2.COLOR_BGR2RGB), "Đọc màu BGR bằng OpenCV")
			self._show_array("brightness_original", cv2.cvtColor(image, cv2.COLOR_BGR2RGB), self._dimensions(image))
			self._show_array("geometry_original", cv2.cvtColor(image, cv2.COLOR_BGR2RGB), self._dimensions(image))
			self._update_geometry()
			if Image is not None and ImageTk is not None:
				try:
					with Image.open(path) as pil_image:
						pil_rgb = pil_image.convert("RGB")
						self._show_pil_image("pillow", pil_rgb, f"{pil_rgb.width} × {pil_rgb.height} px")
				except OSError as error:
					self._set_placeholder("pillow", f"Pillow không đọc được ảnh: {error}")
			else:
				self._set_placeholder("pillow", "Cài Pillow để xem ảnh đọc bằng PIL.")
			self.preview_details["opencv"].configure(text=self._dimensions(image))
			self._update_adjustments()
		else:
			self.second_path = Path(path)
			self.second_image = image
			self._show_array("second", cv2.cvtColor(image, cv2.COLOR_BGR2RGB), self._dimensions(image))
			self._set_placeholder("and", "Bấm Phân tích ảnh để cập nhật AND.")

		self._update_file_names()
		self.status_text.set(f"Đã nạp ảnh {image_number}: {Path(path).name}")

	def choose_first(self):
		self._choose_image(1)

	def choose_second(self):
		self._choose_image(2)

	def _on_adjustment_change(self, label, value):
		self._update_adjustments()
		if self.image is not None:
			unit = "" if label == "Sáng / tối" else "%"
			self.status_text.set(f"{label}: {float(value):g}{unit}")

	def _update_adjustments(self):
		if self.image is None:
			return
		brightness = self.brightness_value.get()
		contrast = self.contrast_value.get() / 100
		saturation = self.saturation_value.get() / 100
		adjusted = (self.image.astype(np.float32) - 127.5) * contrast + 127.5 + brightness
		adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
		if saturation != 1.0:
			hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV)
			hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.float32) * saturation, 0, 255).astype(np.uint8)
			adjusted = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
		self._show_array(
			"bright",
			cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB),
			f"Sáng/tối {brightness:+d} · tương phản {self.contrast_value.get()}% · bão hòa {self.saturation_value.get()}%",
		)

	def _clear_processed_previews(self):
		for key in (
			"gray",
			"hue",
			"saturation",
			"value",
			"and",
			"bright",
			"rotate",
			"translate",
			"zoom",
		):
			self._set_placeholder(key, "Bấm Phân tích ảnh để tạo kết quả.")

	def reset(self):
		self.image_path = None
		self.second_path = None
		self.image = None
		self.second_image = None
		self.brightness_value.set(0)
		self.contrast_value.set(100)
		self.saturation_value.set(100)
		self.zoom_value.set(1.0)
		self.rotation_value.set(0)
		self.offset_x_value.set(0)
		self.offset_y_value.set(0)
		self._update_file_names()
		for key in self.preview_labels:
			self._set_placeholder(key, "Chưa có ảnh")
		self.status_text.set("Đã đặt lại. Chọn ảnh mới để bắt đầu phân tích.")

	def analyze(self):
		if self.image is None:
			messagebox.showinfo("Chưa có ảnh", "Hãy chọn ảnh 1 trước khi phân tích.")
			return

		gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
		hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
		hue, saturation, value = cv2.split(hsv)
		hue_display = cv2.applyColorMap(hue, cv2.COLORMAP_HSV)
		hue_display = cv2.cvtColor(hue_display, cv2.COLOR_BGR2RGB)
		self._show_array("gray", gray, f"{gray.shape[1]} × {gray.shape[0]} px · 8-bit")
		self._show_array("hue", hue_display, "H: 0–179 · tô màu giả để dễ quan sát")
		self._show_array("saturation", saturation, "S: 0–255 · grayscale")
		self._show_array("value", value, "V: 0–255 · grayscale")
		self._update_adjustments()
		self._update_geometry()

		if self.second_image is None:
			self._set_placeholder("and", "Chọn ảnh 2 để tạo kết quả AND.")
			self.status_text.set("Đã tạo các kết quả màu, độ sáng và hình học. Chọn ảnh 2 để thực hiện AND.")
			return

		second = self.second_image
		resized = second.shape[:2] != self.image.shape[:2]
		if resized:
			second = cv2.resize(second, (self.image.shape[1], self.image.shape[0]))
		result = cv2.bitwise_and(self.image, second)
		detail = self._dimensions(result)
		if resized:
			detail += " · ảnh 2 đã co giãn để khớp kích thước"
		self._show_array("and", cv2.cvtColor(result, cv2.COLOR_BGR2RGB), detail)
		self.status_text.set("Phân tích hoàn tất: màu, độ sáng, hình học và Bitwise AND.")

	def _on_geometry_change(self, value):
		self._update_geometry()
		if self.image is not None:
			self.status_text.set(f"Đã cập nhật biến đổi: {float(value):g}.")

	def _update_geometry(self):
		if self.image is None:
			return

		height, width = self.image.shape[:2]
		angle = self.rotation_value.get()
		center = (width / 2, height / 2)
		rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
		cosine = abs(rotation_matrix[0, 0])
		sine = abs(rotation_matrix[0, 1])
		rotated_width = int(np.ceil((height * sine) + (width * cosine) - 1e-10))
		rotated_height = int(np.ceil((height * cosine) + (width * sine) - 1e-10))
		rotation_matrix[0, 2] += (rotated_width / 2) - center[0]
		rotation_matrix[1, 2] += (rotated_height / 2) - center[1]
		rotated = cv2.warpAffine(self.image, rotation_matrix, (rotated_width, rotated_height))
		self._show_array(
			"rotate",
			cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB),
			f"Góc {angle}° · {self._dimensions(rotated)}",
		)

		offset_x = self.offset_x_value.get()
		offset_y = self.offset_y_value.get()
		translation_matrix = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
		translated = cv2.warpAffine(self.image, translation_matrix, (width, height))
		self._show_array(
			"translate",
			cv2.cvtColor(translated, cv2.COLOR_BGR2RGB),
			f"X: {offset_x} px · Y: {offset_y} px · {self._dimensions(translated)}",
		)

		zoom = self.zoom_value.get()
		zoomed = cv2.resize(self.image, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_LINEAR)
		self._show_array(
			"zoom",
			cv2.cvtColor(zoomed, cv2.COLOR_BGR2RGB),
			f"Tỷ lệ {zoom:.1f}× · {self._dimensions(zoomed)}",
		)

	def save_formats(self):
		if self.image is None or self.image_path is None:
			messagebox.showinfo("Chưa có ảnh", "Hãy chọn ảnh 1 trước khi lưu.")
			return

		folder = filedialog.askdirectory(title="Chọn thư mục lưu ảnh")
		if not folder:
			return

		stem = self.image_path.stem
		saved = []
		failed = []
		for extension in ("png", "jpg", "bmp"):
			output_path = Path(folder) / f"{stem}.{extension}"
			if cv2.imwrite(str(output_path), self.image):
				saved.append(output_path.name)
			else:
				failed.append(output_path.name)

		if failed:
			messagebox.showerror("Lưu chưa hoàn tất", "Không thể lưu: " + ", ".join(failed))
		else:
			messagebox.showinfo("Đã lưu ảnh", "Đã lưu PNG, JPEG và BMP vào:\n" + folder)
			self.status_text.set(f"Đã lưu {len(saved)} định dạng trong {folder}")

	def _show_array(self, key, array, detail):
		if Image is None or ImageTk is None:
			self._set_placeholder(key, "Cài Pillow để hiển thị ảnh trong bảng.")
			return
		self._show_pil_image(key, Image.fromarray(array), detail)

	def _show_pil_image(self, key, image, detail):
		if Image is None or ImageTk is None:
			return
		preview = image.copy()
		preview.thumbnail((340, 205), Image.Resampling.LANCZOS)
		photo = ImageTk.PhotoImage(preview)
		self.preview_photos[key] = photo
		self.preview_labels[key].configure(image=photo, text="", width=1, height=1)
		self.preview_details[key].configure(text=detail)

	def _set_placeholder(self, key, text):
		self.preview_labels[key].configure(image="", text=text, width=34, height=9)
		self.preview_details[key].configure(text="")
		self.preview_photos.pop(key, None)

	def _dimensions(self, image):
		return f"{image.shape[1]} × {image.shape[0]} px"

	def _update_file_names(self):
		first = self.image_path.name if self.image_path else "chưa chọn ảnh 1"
		second = self.second_path.name if self.second_path else "chưa chọn ảnh 2"
		self.files_text.set(f"Ảnh 1: {first}     |     Ảnh 2: {second}")


if __name__ == "__main__":
	root = tk.Tk()
	app = ImageProcessingApp(root)
	root.mainloop()
