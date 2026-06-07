# OMR

Aplicação OMR local (desktop-first), sem servidor externo.

## Estrutura

```
omr-system/
├── backend/
│   ├── app.py
│   ├── omr.py
│   ├── pdf_gen.py
│   ├── models.py
│   └── database.db
├── frontend/
│   └── OMRDesktopApp.java
├── uploads/
├── outputs/
└── run.py
```

## Como executar localmente

1. Instale dependências Python:
   - Flask
   - opencv-contrib-python
   - reportlab
2. Rode a API local:

```bash
python run.py
```

3. Em outro terminal, compile e execute o frontend Java:

```bash
cd frontend
javac OMRDesktopApp.java
java OMRDesktopApp
```

A API sobe em `localhost:5000` e o frontend roda como app desktop Java.

## Validação do motor OMR antes da interface

Você pode testar primeiro só o motor:

```bash
python -m backend.omr /caminho/para/foto.jpg --questions 10 --choices 5
```

Esse fluxo ajuda a validar a detecção com confiança antes de evoluir a interface.
