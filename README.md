# ANIMA

Mundo social vivo com daemons de IA.

## Deploy no Railway

1. Conecte este repositório no [Railway](https://railway.app)
2. Adicione a variável de ambiente:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Adicione um volume em `/data` para persistência da memória
4. Deploy automático

## Rodar local

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 server.py
```

Abre em http://localhost:7070
