import tkinter as tk

root = tk.Tk()
root.title("Scroll con Frame dentro de Canvas")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# Canvas principal
canvas = tk.Canvas(main_frame, bg="lightgray")
canvas.pack(side="left", fill="both", expand=True)

# Scrollbar vertical
scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.configure(yscrollcommand=scrollbar.set)

# Frame interno
inner_frame = tk.Frame(canvas, bg="white")
canvas.create_window((0, 0), window=inner_frame, anchor="nw")

# Agregar varios widgets
for i in range(20):
    tk.Label(inner_frame, text=f"Item {i+1}", bg="white").pack(pady=5, padx=10)

# Ajustar el área desplazable cuando cambie el tamaño del frame interno
def update_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

inner_frame.bind("<Configure>", update_scroll_region)

root.mainloop()
