import tkinter as tk
from tkinter import filedialog, messagebox
import os
import base64
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import io
import sounddevice as sd
from tkinter.ttk import Progressbar, Style
import threading

# Variables globales
audio_data = None
fs = None
playing = False  # Pour gérer le statut play/pause
file_name = None  # Nom du fichier chargé
progress_bar = None
audio_duration = 0  # Durée de l'audio en secondes
current_position = 0  # Position actuelle de la lecture
data_dtype = None  # Type des données audio

def decode_b64_to_wav(b64_data):
    try:
        # Convertir le fichier b64 en wav
        audio_decoded = base64.b64decode(b64_data)
        audio_io = io.BytesIO(audio_decoded)
        return audio_io
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la conversion du fichier : {e}")
        return None

def process_audio(audio_io):
    global audio_data, fs, audio_duration, current_position, data_dtype
    
    try:
        # Lire les données audio directement en utilisant scipy.io.wavfile.read
        fs, audio_data = wavfile.read(audio_io)
        data_dtype = audio_data.dtype
        audio_duration = len(audio_data) / fs  # Durée totale de l'audio en secondes
        current_position = 0  # Réinitialiser la position de la lecture

        # Calculer le spectrogramme
        frequency_range, time_range, spectrogram_matrix = signal.spectrogram(audio_data, fs=fs)
        spectrogram_matrix = np.array(spectrogram_matrix)

        # Calculer le DSE
        dse = np.sum(spectrogram_matrix, axis=1)
        
        # Calculer le signal temporel
        temporal = np.sum(spectrogram_matrix, axis=0)

        # Afficher les graphiques
        fig, axs = plt.subplots(3, 1, figsize=(10, 10))
        axs[0].plot(dse)
        axs[0].set_title(f"DSE de l'audio")
        axs[1].imshow(spectrogram_matrix, aspect="auto", cmap="inferno", origin="lower", vmin=0, vmax=10*np.mean(spectrogram_matrix))
        axs[1].set_title("Spectrogramme")
        axs[2].plot(temporal)
        axs[2].set_title("Temporel")
        plt.show()

        # Initialiser la barre de progression
        progress_bar['maximum'] = audio_duration

    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du traitement de l'audio : {e}")

def update_progress():
    global current_position
    while playing and current_position <= audio_duration:
        progress_bar['value'] = current_position
        current_position += 0.1  # Mise à jour toutes les 100ms
        root.update()
        root.after(100)

def play_pause_audio():
    global playing
    if audio_data is not None:
        if not playing:
            sd.play(audio_data, fs)
            playing = True
            play_button.config(text="Pause")
            threading.Thread(target=update_progress).start()
        else:
            sd.stop()
            playing = False
            play_button.config(text="Play")

def save_audio():
    if audio_data is not None and fs is not None:
        save_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("Wav files", "*.wav")])
        if save_path:
            try:
                # Utiliser scipy.io.wavfile.write pour sauvegarder l'audio
                wavfile.write(save_path, fs, audio_data)
                messagebox.showinfo("Succès", "Audio enregistré avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement : {e}")
    else:
        messagebox.showwarning("Avertissement", "Aucun fichier audio à sauvegarder.")

def select_file():
    global file_name
    file_path = filedialog.askopenfilename(title="Sélectionner un fichier b64", filetypes=[("Text Files", "*.txt")])
    if not file_path:
        return

    with open(file_path, "r") as file:
        b64_data = file.read()

    audio_io = decode_b64_to_wav(b64_data)
    if audio_io:
        process_audio(audio_io)
        file_name = os.path.basename(file_path)
        file_label.config(text=f"Fichier chargé : {file_name}")

# Interface graphique améliorée
root = tk.Tk()
root.title("Audio Processor")
root.geometry("400x300")
root.configure(bg='#f0f0f0')

# Styles pour les boutons et la barre de progression
style = Style()
style.configure("TButton", font=("Arial", 12), padding=6)
style.configure("TProgressbar", thickness=20)

# Afficher le nom du fichier chargé avec une police plus grande
file_label = tk.Label(root, text="Aucun fichier chargé", font=("Arial", 12), bg='#f0f0f0', pady=10)
file_label.pack()

# Boutons pour les actions avec plus de style
select_button = tk.Button(root, text="Sélectionner un fichier", font=("Arial", 12), command=select_file, padx=10, pady=5, bg="#4CAF50", fg="white")
select_button.pack(pady=10)

play_button = tk.Button(root, text="Play", font=("Arial", 12), command=play_pause_audio, padx=10, pady=5, bg="#008CBA", fg="white")
play_button.pack(pady=10)

save_button = tk.Button(root, text="Sauvegarder l'audio", font=("Arial", 12), command=save_audio, padx=10, pady=5, bg="#f44336", fg="white")
save_button.pack(pady=10)

# Barre de progression avec style amélioré
progress_bar = Progressbar(root, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
progress_bar.pack(pady=20)

root.mainloop()