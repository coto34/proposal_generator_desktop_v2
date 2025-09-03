import os
import tkinter as tk
from ui.wizard import ProposalWizard
from dotenv import load_dotenv

def main():
    load_dotenv()
    root = tk.Tk()
    root.title("Generador de Propuestas")
    root.geometry("1100x720")
    root.minsize(1000, 650)
    app = ProposalWizard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
