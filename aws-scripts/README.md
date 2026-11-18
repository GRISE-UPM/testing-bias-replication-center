# Scripts de AWS (Learner Lab)

Requisitos: AWS CLI configurado (`aws sts get-caller-identity` responde) y Git Bash en Windows.
Las credenciales del Learner Lab duran 4 h; nunca se guardan en el repositorio.

    ./aws-scripts/cognito.sh create   # User Pool + App Client + dominio Hosted UI
    ./aws-scripts/cognito.sh show     # muestra IDs (no son secretos)
    ./aws-scripts/cognito.sh delete   # borra todo

El App Client es publico (sin secret), flujo `code` con PKCE, scopes `openid email profile`
y URL de retorno `http://localhost:4200` (unica HTTP que Cognito admite).
Los IDs generados quedan en `aws-scripts/cognito.generated.env` (ignorado por git).
