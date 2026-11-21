#!/usr/bin/env bash
# Crea (o borra) el User Pool, el App Client y el dominio Hosted UI de Cognito
# para el portal. Pensado para AWS Academy Learner Lab (us-east-1).
# Uso:  ./aws-scripts/cognito.sh create | groups | organizer <correo> | show | delete
# En Windows, ejecutar desde Git Bash. No imprime credenciales.
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
POOL_NAME="portal-replicacion-pool"
CLIENT_NAME="portal-replicacion-spa"
CALLBACK="${CALLBACK_URL:-http://localhost:4200}"
OUT="aws-scripts/cognito.generated.env"   # ignorado por git

account() { aws sts get-caller-identity --query Account --output text; }

pool_id() {
  aws cognito-idp list-user-pools --max-results 60 --region "$REGION" \
    --query "UserPools[?Name=='$POOL_NAME'].Id | [0]" --output text
}

create() {
  EXISTING=$(pool_id)
  if [ "$EXISTING" != "None" ]; then
    echo "Ya existe el User Pool $EXISTING. Usa 'delete' primero o 'show'."; exit 1
  fi
  ACCOUNT=$(account)
  DOMAIN="portal-replicacion-$ACCOUNT"

  POOL_ID=$(aws cognito-idp create-user-pool --region "$REGION" \
    --pool-name "$POOL_NAME" \
    --auto-verified-attributes email \
    --username-attributes email \
    --admin-create-user-config AllowAdminCreateUserOnly=false \
    --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":false}}' \
    --query UserPool.Id --output text)
  echo "User Pool: $POOL_ID"

  # Cliente publico (SPA): sin secret, flujo code + PKCE, scopes de identidad.
  CLIENT_ID=$(aws cognito-idp create-user-pool-client --region "$REGION" \
    --user-pool-id "$POOL_ID" \
    --client-name "$CLIENT_NAME" \
    --no-generate-secret \
    --allowed-o-auth-flows code \
    --allowed-o-auth-scopes openid email profile \
    --allowed-o-auth-flows-user-pool-client \
    --callback-urls "$CALLBACK" \
    --logout-urls "$CALLBACK" \
    --supported-identity-providers COGNITO \
    --refresh-token-validity 30 \
    --query UserPoolClient.ClientId --output text)
  echo "App Client: $CLIENT_ID"

  aws cognito-idp create-user-pool-domain --region "$REGION" \
    --domain "$DOMAIN" --user-pool-id "$POOL_ID" >/dev/null
  echo "Dominio: $DOMAIN"

  cat > "$OUT" <<EOT
COGNITO_REGION=$REGION
COGNITO_USER_POOL_ID=$POOL_ID
COGNITO_CLIENT_ID=$CLIENT_ID
COGNITO_ISSUER=https://cognito-idp.$REGION.amazonaws.com/$POOL_ID
COGNITO_DOMAIN=https://$DOMAIN.auth.$REGION.amazoncognito.com
EOT
  echo "Configuracion escrita en $OUT"
  groups
}

# Grupos del portal: organizer (organizadores) y participant (investigadores validados).
groups() {
  POOL_ID=$(pool_id)
  [ "$POOL_ID" = "None" ] && { echo "Primero ejecuta 'create'."; exit 1; }
  for G in organizer participant; do
    aws cognito-idp create-group --region "$REGION" --user-pool-id "$POOL_ID" \
      --group-name "$G" >/dev/null 2>&1 && echo "Grupo creado: $G" || echo "Grupo ya existe: $G"
  done
}

# Convierte en organizador a un usuario que ya se registro (el correo es su nombre de usuario).
organizer() {
  EMAIL="${1:?Uso: $0 organizer <correo>}"
  POOL_ID=$(pool_id)
  [ "$POOL_ID" = "None" ] && { echo "Primero ejecuta 'create'."; exit 1; }
  aws cognito-idp admin-add-user-to-group --region "$REGION" --user-pool-id "$POOL_ID" \
    --username "$EMAIL" --group-name organizer
  echo "$EMAIL es ahora organizador. Debe cerrar sesion y volver a entrar."
}

delete() {
  POOL_ID=$(pool_id)
  [ "$POOL_ID" = "None" ] && { echo "No hay User Pool que borrar."; exit 0; }
  DOMAIN=$(aws cognito-idp describe-user-pool --region "$REGION" \
    --user-pool-id "$POOL_ID" --query UserPool.Domain --output text)
  [ "$DOMAIN" != "None" ] && aws cognito-idp delete-user-pool-domain \
    --region "$REGION" --domain "$DOMAIN" --user-pool-id "$POOL_ID"
  aws cognito-idp delete-user-pool --region "$REGION" --user-pool-id "$POOL_ID"
  rm -f "$OUT"
  echo "Borrado $POOL_ID"
}

case "${1:-}" in
  create) create ;;
  groups) groups ;;
  organizer) organizer "${2:-}" ;;
  delete) delete ;;
  show) [ -f "$OUT" ] && cat "$OUT" || echo "Aun no hay configuracion generada." ;;
  *) echo "Uso: $0 create|groups|organizer <correo>|show|delete"; exit 1 ;;
esac
