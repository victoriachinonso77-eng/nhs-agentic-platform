#!/bin/bash
echo "Starting all NHS AI Platform simulations..."

streamlit run app_v2_clinical.py --server.port 8501 &
sleep 2

streamlit run documentation_simulation.py --server.port 8502 &
sleep 2

streamlit run handover_simulation.py --server.port 8503 &
sleep 2

streamlit run workflow_simulation.py --server.port 8504 &
sleep 2

streamlit run cognitive_simulation.py --server.port 8505 &
sleep 2

streamlit run integration_simulation.py --server.port 8506 &
sleep 2

streamlit run coordination_simulation.py --server.port 8507 &
sleep 2

streamlit run security_simulation.py --server.port 8508 &
sleep 2

streamlit run full_shift_simulation.py --server.port 8509 &

echo ""
echo "========================================="
echo " ALL NHS AI PLATFORM APPS RUNNING"
echo "========================================="
echo " Main Platform:        http://localhost:8501"
echo " Documentation Agent:  http://localhost:8502"
echo " Handover Agent:       http://localhost:8503"
echo " Workflow Agent:       http://localhost:8504"
echo " Cognitive Agent:      http://localhost:8505"
echo " Integration Agent:    http://localhost:8506"
echo " Coordination Agent:   http://localhost:8507"
echo " Security Agent:       http://localhost:8508"
echo " Full Shift (07-19h):  http://localhost:8509"
echo "========================================="
echo " Each page now has a chat box at the bottom"
echo " Press Ctrl+C to stop all"
echo "========================================="
wait
