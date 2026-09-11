import tkinter as tk
import time

def create_orb():
    root = tk.Tk()
    root.overrideredirect(True) # Borderless
    root.geometry("100x100+100+100") # Small square, top left
    root.attributes('-topmost', True) # Always on top
    
    # Make black background transparent (Windows specific)
    root.config(bg='black')
    root.wm_attributes('-transparentcolor', 'black')

    canvas = tk.Canvas(root, width=100, height=100, bg='black', highlightthickness=0)
    canvas.pack()

    # Draw a blue orb
    orb = canvas.create_oval(10, 10, 90, 90, fill="cyan", outline="blue", width=2)

    # Pulse animation
    def pulse():
        for i in range(10):
            canvas.coords(orb, 10+i, 10+i, 90-i, 90-i)
            root.update()
            time.sleep(0.05)
        for i in range(10, 0, -1):
            canvas.coords(orb, 10+i, 10+i, 90-i, 90-i)
            root.update()
            time.sleep(0.05)
        root.after(100, pulse)

    root.after(100, pulse)
    
    # Close after 5 seconds for test
    root.after(5000, root.destroy)
    root.mainloop()

if __name__ == '__main__':
    create_orb()
