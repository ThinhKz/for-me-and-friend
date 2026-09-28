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

		brightness_controls = tk.Frame(brightness_tab, bg="#f2f4f1", padx=14, pady=8)
		brightness_controls.pack(fill="x")
		tk.Label(
			brightness_controls,
			text="Cộng độ sáng vào mỗi pixel",
			font=("Segoe UI", 9, "bold"),
			background="#f2f4f1",
			foreground="#375149",
		).pack(side="left", padx=(0, 16))
		tk.Label(
			brightness_controls,
			text="0",
			font=("Segoe UI", 9),
			background="#f2f4f1",
			foreground="#375149",
		).pack(side="left")
		tk.Scale(
			brightness_controls,
			from_=0,
			to=100,
			variable=self.brightness_value,
			command=self._on_brightness_change,
		).pack(side="left", fill="x", expand=True, padx=8)
		tk.Label(
			brightness_controls,
			text="100",
			font=("Segoe UI", 9),
			background="#f2f4f1",
			foreground="#375149",
		).pack(side="left")
		self._create_gallery(
			brightness_tab,
			[
				("brightness_original", "ẢNH GỐC"),
				("bright", "ẢNH TĂNG SÁNG"),
			],
			columns=2,
		)
		self._create_gallery(
			geometry_tab,
			[
				("geometry_original", "ẢNH GỐC"),
				("rotate90", "XOAY 90° THEO CHIỀU KIM ĐỒNG HỒ"),
				("rotate180", "XOAY 180°"),
				("translate", "DỊCH PHẢI 50 PX"),
				("zoom", "PHÓNG TO 1.5×"),
			],
			columns=3,
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
			self._update_brightness()
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

	def _on_brightness_change(self, value):
		self._update_brightness(round(float(value)))

	def _update_brightness(self, delta=None):
		if self.image is None:
			return
		if delta is None:
			delta = self.brightness_value.get()
		bright = cv2.addWeighted(self.image, 1.0, self.image, 0.0, delta)
		self._show_array(
			"bright",
			cv2.cvtColor(bright, cv2.COLOR_BGR2RGB),
			f"Cộng {delta} vào mỗi kênh · giới hạn tối đa 255",
		)

	def _clear_processed_previews(self):
		for key in (
			"gray",
			"hue",
			"saturation",
			"value",
			"and",
			"bright",
			"rotate90",
			"rotate180",
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
		self._update_brightness()

		rotated_90 = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
		rotated_180 = cv2.rotate(self.image, cv2.ROTATE_180)
		height, width = self.image.shape[:2]
		translation_matrix = np.float32([[1, 0, 50], [0, 1, 0]])
		translated = cv2.warpAffine(self.image, translation_matrix, (width, height))
		zoomed = cv2.resize(self.image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
		self._show_array(
			"rotate90",
			cv2.cvtColor(rotated_90, cv2.COLOR_BGR2RGB),
			f"Theo chiều kim đồng hồ · {self._dimensions(rotated_90)}",
		)
		self._show_array(
			"rotate180",
			cv2.cvtColor(rotated_180, cv2.COLOR_BGR2RGB),
			self._dimensions(rotated_180),
		)
		self._show_array(
			"translate",
			cv2.cvtColor(translated, cv2.COLOR_BGR2RGB),
			"Dịch phải 50 px · phần trống được tô đen",
		)
		self._show_array(
			"zoom",
			cv2.cvtColor(zoomed, cv2.COLOR_BGR2RGB),
			f"Tỷ lệ 1.5× · {self._dimensions(zoomed)}",
		)

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
