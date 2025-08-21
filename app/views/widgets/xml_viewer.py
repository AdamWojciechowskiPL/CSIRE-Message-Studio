# csire_message_studio/app/views/widgets/xml_viewer.py
import tkinter as tk
from tkinter import ttk
from pygments import lex
from pygments.lexers.html import XmlLexer
from pygments.styles import get_style_by_name

class XmlViewer(ttk.Frame):
    """Ramka zawierająca widget Text z podświetlaniem składni XML i pionowym paskiem przewijania."""
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # 1. Utworzenie paska przewijania
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)

        # 2. Utworzenie widgetu Text i połączenie go z paskiem przewijania
        self.text_widget = tk.Text(
            self,
            wrap=tk.NONE,
            undo=False,
            font=("Courier New", 10),
            yscrollcommand=self.scrollbar.set
        )

        # 3. Skonfigurowanie komendy paska, aby przewijał widget Text
        self.scrollbar.config(command=self.text_widget.yview)

        # 4. Umieszczenie widgetów w ramce
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Inicjalizacja podświetlania składni
        self.lexer = XmlLexer()
        self.style = get_style_by_name('default')
        self._configure_tags()
        
        self.text_widget.config(state=tk.DISABLED)

    def _configure_tags(self):
        """Tworzy tagi Tkinter na podstawie definicji stylu Pygments."""
        for token, style in self.style:
            tag_name = str(token)
            foreground = style['color']
            if foreground:
                self.text_widget.tag_configure(tag_name, foreground=f"#{foreground}")

    def show_xml(self, xml_string: str):
        """Wyświetla sformatowany ciąg XML z podświetlaniem składni."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete('1.0', tk.END)

        if not xml_string:
            self.text_widget.config(state=tk.DISABLED)
            return

        tokens = lex(xml_string, self.lexer)
        
        for token_type, token_text in tokens:
            self.text_widget.insert(tk.END, token_text, (str(token_type),))
            
        self.text_widget.config(state=tk.DISABLED)

    def get_content(self) -> str:
        """Zwraca całą zawartość widgetu jako string."""
        return self.text_widget.get('1.0', tk.END).strip()