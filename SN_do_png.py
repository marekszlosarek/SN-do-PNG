import os
import tkinter as tk
from tkinter import scrolledtext, ttk
from dotenv import load_dotenv
import pyperclip

load_dotenv()

DXF_PATH = os.getenv("DXF_PATH")
PNG_PATH = os.getenv("PNG_PATH")
IGNORED_FOLDERS = os.getenv("IGNORED_FOLDERS", "[]")


class Window(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Konwerter SNów do karty modułu')

        self.sn_dict = {}
        self.images = []

        self.mainframe = tk.Frame(self)
        self.mainframe.pack()

        self.snText = scrolledtext.ScrolledText(self.mainframe, width=25, height=16, wrap=tk.WORD)
        self.snText.grid(row=1, column=0, padx=3, pady=3, rowspan=3)

        self.snLabel = tk.Label(self.mainframe, text='Wklej SNy z Karty Modułu:', font=['arial', 12, 'italic'], width=30)
        self.snLabel.grid(row=0, column=0, sticky='w', padx=3, pady=3)

        self.convertButton = tk.Button(self.mainframe, text='Konwertuj', font=['arial', 12, 'bold'], command=self.find_materials_and_convert)
        self.convertButton.grid(row=1, column=1, padx=3, pady=3)

        self.pngLabel = tk.Label(self.mainframe, text='Konwertuj i wklej do Karty Modułu:', font=['arial', 12, 'italic'], width=30)
        self.pngLabel.grid(row=0, column=2, sticky='w', padx=3, pady=3)
        
        self.pngText = scrolledtext.ScrolledText(self.mainframe, width=25, height=16, wrap=tk.WORD, state=tk.DISABLED)
        self.pngText.grid(row=1, column=2, padx=3, pady=3, rowspan=3)

        self.materialLabel = tk.Label(self.mainframe, text='Wybierz materiał:\n\n\n')
        self.materialLabel.grid(row=2, column=1, padx=3, pady=3)

        self.materialVar = tk.StringVar()
        self.materialCombo = ttk.Combobox(self.mainframe, textvariable=self.materialVar)
        self.materialCombo.grid(row=2, column=1, padx=3, pady=3)
        self.materialCombo.bind("<<ComboboxSelected>>", self.generate_png_list)

        self.pasteButton = tk.Button(self.mainframe, text="Wklej", command=self.paste_sn, font=['arial', 13, ''])
        self.pasteButton.grid(row=5, column=0, padx=3, pady=3)

        self.resetButton = tk.Button(self.mainframe, text="Wyczyść", command=self.reset, font=['arial', 13, ''])
        self.resetButton.grid(row=5, column=1, padx=3, pady=3)

        self.copyButton = tk.Button(self.mainframe, text="Kopiuj", command=self.copy_png, font=['arial', 13, ''])
        self.copyButton.grid(row=5, column=2, padx=3, pady=3)

        self.warningLabelUpper = tk.Label(self.mainframe, font=['arial', 18, 'bold'], text='')
        self.warningLabelUpper.grid(row=6, column=0, padx=3, pady=3, sticky='w', columnspan=3)

        self.warningLabelLower = tk.Label(self.mainframe, font=['arial', 13, ''], text='', height=3, anchor='nw', justify='left')
        self.warningLabelLower.grid(row=7, column=0, padx=3, sticky='nw', columnspan=3)
                

    def find_materials_and_convert(self, event=None):
        self.sn_dict = self.get_sn_dict()
        if len(self.sn_dict) == 0:
            self.reset()
            return
        
        self.convert_SN_to_PNG()
        total_materials = [list(self.sn_dict[sn]) for sn in self.sn_dict.keys() if len(self.sn_dict[sn]) > 0 and sn]

        mutual_materials = \
            [] if total_materials == [] \
            else list(set(total_materials[0]).intersection(*total_materials[1:]))
    
        mutual_materials.append(mutual_materials.pop(mutual_materials.index('Dowolne')))
        self.materialCombo['values'] = mutual_materials
        self.materialCombo.current(0)
        self.generate_png_list()


    def convert_SN_to_PNG(self, event=None):
        for root, dirs, files in os.walk(DXF_PATH, topdown=False):
            for name in files:
                material = root.split('\\')[-1]
                if material in IGNORED_FOLDERS:
                    continue
                if not name.endswith('dxf'):
                    continue
                
                for sn in list(self.sn_dict):
                    if \
                    name.startswith(f'{sn} ') or \
                    name.startswith(f'{sn}-') or \
                    name.startswith(f'{sn}_') or \
                    name.startswith(f'{sn}.') or \
                    name.startswith(f'SN {sn} ') or \
                    name.startswith(f'SN {sn}-') or \
                    name.startswith(f'SN {sn}_') or \
                    name.startswith(f'SN {sn}.'):
                        if material not in self.sn_dict[sn]:
                            self.sn_dict[sn][material] = []
                        self.sn_dict[sn][material].append(name.replace('.dxf', ''))
                        self.sn_dict[sn]['Dowolne'].append(name.replace('.dxf', ''))


    def generate_png_list(self, event=None):
        self.images = []
        warnings = []
        noPart = False
        noDxf = False

        material = self.materialCombo.get()
        self.warningLabelUpper.configure(text='')
        self.warningLabelLower.configure(text='')

        if material:
            details = {sn: self.sn_dict[sn][material] for sn in list(self.sn_dict) if sn}
        else:
            details = {sn: self.sn_dict[sn]['Dowolne'] for sn in list(self.sn_dict) if sn}
   
        self.pngText.config(state=tk.NORMAL)
        self.pngText.delete("1.0", tk.END)
        for line, sn in enumerate(self.get_sn_list()):
            snImage = ''

            ## Pusta linia
            if sn == '':
                self.pngText.insert(tk.END, '\n')
                self.images.append(snImage)
                continue
            
            ## Brak DXFa 
            if len(details[sn]) == 0:
                snImage = '!!! Brak DXF !!!'
                self.pngText.insert(tk.END, snImage+'\n' if len(snImage) <= 25 else snImage[:22]+'...\n')
                self.pngText.tag_add(sn, f'{line+1}.0', f'{line+1}.end')
                self.pngText.tag_configure(sn, background='red', foreground='white')
                noDxf = True
                self.images.append(snImage)
                continue

            ## Sukces w szukaniu
            for image in details[sn]:
                found = False
                if os.path.exists(os.path.join(PNG_PATH, image+'.png')):
                    snImage = image
                    self.pngText.insert(tk.END, snImage+'\n' if len(snImage) <= 25 else snImage[:22]+'...\n')
                    self.pngText.tag_add(sn, f'{line+1}.0', f'{line+1}.end')
                    self.pngText.tag_configure(sn, background='#bccc74')
                    self.images.append(snImage)
                    break
                imageStart = image.replace(' ', '_').split('_')[0] if not image.startswith('SN ') else image.replace(' ', '_').split('_')[1]
                with os.scandir(PNG_PATH) as images:
                    for image_entry in images:
                        if image_entry.is_file() and image_entry.name.startswith(imageStart) and image_entry.name.endswith('.png'):
                            image = image_entry.name.removesuffix('.png')
                            snImage = image
                            self.pngText.insert(tk.END, snImage+'\n' if len(snImage) <= 25 else snImage[:22]+'...\n')
                            self.pngText.tag_add(sn, f'{line+1}.0', f'{line+1}.end')
                            self.pngText.tag_configure(sn, background='#bccc74')
                            self.images.append(snImage)
                            found = True
                            break
                    if found:
                        break
            
            ## Brak parta
            if not snImage:
                snImage = image
                self.pngText.insert(tk.END, snImage+'\n' if len(snImage) <= 25 else snImage[:22]+'...\n')
                self.pngText.tag_add(sn, f'{line+1}.0', f'{line+1}.end')
                self.pngText.tag_configure(sn, background='#FFCCCC')
                noPart = True
                self.images.append(snImage)
                continue
        self.pngText.config(state=tk.DISABLED)

        if noPart:
            warnings.append("- Jeden lub więcej zaplanowanych SNów nie ma stworzonych Partów,\nkarty nie będą mogły być wydrukowane.")
        if noDxf:
            warnings.append("- Jeden lub więcej zaplanowanych SNów nie ma stworzonych DXFów.")
        if len(warnings) > 0:
            self.warningLabelUpper.configure(text='Uwaga:')
            self.warningLabelLower.configure(text='\n'.join(warnings))
            

    def get_sn_dict(self):
        return {sn:{'Dowolne':[]} for sn in self.get_sn_list()}
    

    def get_sn_list(self):

        sn_list = self.snText.get('1.0', tk.END).split('\n')
        try:
            while sn_list[-1] == '':
                sn_list.pop()
        except IndexError:
            return {}

        for index, sn in enumerate(sn_list):
            sn_list[index] = sn.replace('SN ', '').strip()

        return sn_list


    def copy_png(self, event=None):
        pyperclip.copy('\n'.join(self.images))

    def paste_sn(self, event=None):
        self.reset()
        self.snText.insert('1.0', pyperclip.paste())

    def reset(self, event=None):
        self.snText.delete("1.0", tk.END)
        self.pngText.config(state=tk.NORMAL)
        self.pngText.delete("1.0", tk.END)
        self.pngText.config(state=tk.DISABLED)
        self.materialCombo['values'] = []
        self.materialCombo.set('')
        self.warningLabelLower.config(text='')
        self.warningLabelUpper.config(text='')

                        

if __name__ == "__main__":
    win = Window()
    win.mainloop()
