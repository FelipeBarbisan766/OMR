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
│   ├── index.html
│   └── pages/
├── uploads/
├── outputs/
└── run.py
```

## Como executar localmente

1. Instale dependências Python:
   - Flask
   - opencv-contrib-python
   - reportlab
2. Rode:

```bash
python run.py
```

O app sobe em `localhost:5000`, abre no navegador local e encerra junto com o processo.

## Validação do motor OMR antes da interface

Você pode testar primeiro só o motor:

```bash
python -m backend.omr /caminho/para/foto.jpg --questions 10 --choices 5
```

Esse fluxo ajuda a validar a detecção com confiança antes de evoluir a interface.
