@echo off
netconvert --node-files=aye_nodes_nod.xml --edge-files=aye_edges_edg.xml --connection-files=aye_connections_con.xml --output-file=aye_bottleneck_net.xml --offset.disable-normalization true --lefthand true --tls.guess true --no-turnarounds true
if %errorlevel%==0 (echo Network built!) else (echo FAILED!)
pause
