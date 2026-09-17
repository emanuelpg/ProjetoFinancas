from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import socket
import threading
from PIL import Image

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Captura de Cupom</title>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f4f4f9; }
        .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; max-width: 90%; width: 320px; }
        h2 { color: #333; margin-bottom: 1rem; }
        label { display: block; background: #007bff; color: white; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        input[type="file"] { display: none; }
        #status { margin-top: 1rem; font-weight: bold; color: #555; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Foto do Cupom</h2>
        <label for="fotoInput">📸 Abrir Câmera</label>
        <input type="file" id="fotoInput" accept="image/*" capture="environment">
        <div id="status">Aguardando foto...</div>
    </div>

    <script>
        const input = document.getElementById('fotoInput');
        const status = document.getElementById('status');

        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            status.innerText = "Processando e enviando...";

            // Redimensiona no próprio celular para evitar que trave por falta de memória
            const reader = new FileReader();
            reader.onload = function(event) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    const MAX_WIDTH = 1200;
                    let width = img.width;
                    let height = img.height;

                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }

                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    canvas.toBlob(function(blob) {
                        fetch('/upload', {
                            method: 'POST',
                            body: blob
                        }).then(res => {
                            if (res.ok) {
                                status.innerText = "✅ Foto enviada! Pode fechar esta aba.";
                                status.style.color = "green";
                            } else {
                                status.innerText = "❌ Erro ao enviar.";
                                status.style.color = "red";
                            }
                        });
                    }, 'image/jpeg', 0.8);
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        });
    </script>
</body>
</html>
"""


class SimpleUploadHandler(BaseHTTPRequestHandler):
  temp_filename = "imageTest.jpg"
  received = False

  def _set_cors_headers(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "Content-Type")

  def do_OPTIONS(self):
    self.send_response(200)
    self._set_cors_headers()
    self.end_headers()

  def do_GET(self):
    self.send_response(200)
    self.send_header("Content-type", "text/html; charset=utf-8")
    self._set_cors_headers()
    self.end_headers()
    self.wfile.write(HTML_PAGE.encode("utf-8"))

  def do_POST(self):
    if self.path == "/upload":
      try:
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        with open(SimpleUploadHandler.temp_filename, "wb") as f:
          f.write(post_data)

        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(b"OK")
        SimpleUploadHandler.received = True
      except ConnectionResetError:
        # Ignora se o cliente fechar o socket antes do fim
        pass

  def handle(self):
    try:
      super().handle()
    except (ConnectionResetError, ConnectionAbortedError):
      # Evita que o traceback polua o terminal caso o celular feche a aba
      pass

  def log_message(self, format, *args):
    return


class Camera:

  @staticmethod
  def _get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      s.connect(("8.8.8.8", 80))
      ip = s.getsockname()[0]
    except Exception:
      ip = "localhost"
    finally:
      s.close()
    return ip

  @staticmethod
  def upload_url():
    local_ip = Camera._get_local_ip()
    port = 8501

    return(f"http://{local_ip}:{port}")
  
  @staticmethod
  def extract_image(temp_filename="imageTest.jpg") -> Image.Image:
    if os.path.exists(temp_filename):
      os.remove(temp_filename)

    SimpleUploadHandler.temp_filename = temp_filename
    SimpleUploadHandler.received = False

    local_ip = Camera._get_local_ip()
    port = 8501
    server = HTTPServer(("0.0.0.0", port), SimpleUploadHandler)

    print("\n" + "=" * 55)
    print(" [CÂMERA PRONTA] Abra no navegador do celular:")
    print(f" http://{local_ip}:{port}")
    print("=" * 55 + "\n")

    # Inicia o servidor HTTP em background
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    try:
      # Aguarda o sinal de confirmação do upload
      while not SimpleUploadHandler.received:
        threading.Event().wait(0.5)
    finally:
      server.shutdown()
      server.server_close()

    print("Foto capturada com sucesso! Continuando execução...\n")
    return Image.open(temp_filename)