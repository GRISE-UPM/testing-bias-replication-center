# Scripts de AWS (Learner Lab)

Requisitos: AWS CLI configurado (`aws sts get-caller-identity` responde) y Git Bash en Windows.
Las credenciales del Learner Lab duran 4 h; nunca se guardan en el repositorio.

    ./aws-scripts/cognito.sh create   # User Pool + App Client + dominio Hosted UI
    ./aws-scripts/cognito.sh show     # muestra IDs (no son secretos)
    ./aws-scripts/cognito.sh delete   # borra todo

El App Client es publico (sin secret), flujo `code` con PKCE, scopes `openid email profile`
y URL de retorno `http://localhost:4200` (unica HTTP que Cognito admite).
Los IDs generados quedan en `aws-scripts/cognito.generated.env` (ignorado por git).

## Usar Cognito en el portal (desarrollo local)

1. `./aws-scripts/cognito.sh create` (ya crea los grupos `organizer` y `participant`; si el
   pool ya existía, `./aws-scripts/cognito.sh groups`).
2. Backend (el archivo `cognito.generated.env` se lee solo, no hay que copiar IDs):

       cd backend
       pip install -r requirements.txt
       export AUTH_MODE=cognito          # en CMD de Windows: set AUTH_MODE=cognito
       uvicorn app.main:app --reload

3. Frontend: `cd frontend && npm install && npm start` y abrir http://localhost:4200
4. «Log in» → «Sign in» abre la pantalla de Cognito. La primera vez, «Sign up» con tu correo
   (llega un codigo de verificacion).
5. Para ser organizador: `./aws-scripts/cognito.sh organizer tu@correo.com`, cerrar sesion y volver a entrar.

Roles: grupo `organizer` → organizador; grupo `participant` o solicitud aprobada → participante;
cualquier otro usuario autenticado → investigador interesado.
Si el Learner Lab se reinicia y cambia de cuenta, hay que ejecutar `delete` (si aplica) y `create` de nuevo.
