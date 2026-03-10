#!/bin/bash
# Script per aggiornare il componente su Home Assistant

HA_HOST="nicola@192.168.1.251"
HA_PATH="/config/custom_components/climate_group_helper"
LOCAL_PATH="/home/nicola/repo/climate_group_helper/custom_components/climate_group_helper"

echo "Copiando file su Home Assistant..."
scp -r ${LOCAL_PATH}/* ${HA_HOST}:${HA_PATH}/

echo "Verificando versione installata..."
ssh ${HA_HOST} "cd ${HA_PATH} && git log -1 --oneline 2>/dev/null || echo 'Non è un repository git'"

echo "Fatto! Riavvia Home Assistant per applicare le modifiche."
