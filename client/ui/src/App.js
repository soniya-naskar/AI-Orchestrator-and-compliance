import React, {useEffect, useState} from 'react';

function App(){
  const [logs, setLogs] = useState([]);
  useEffect(()=>{
    const ws = new WebSocket('ws://localhost:8000/connect');
    ws.onopen = ()=>{ws.send(JSON.stringify({session_id:'ui-session'}));}
    ws.onmessage = (ev)=>{const m = JSON.parse(ev.data); if(m.type==='hitl_request'){setLogs(prev=>[JSON.stringify(m), ...prev]);}}
    return ()=>ws.close();
  },[]);
  return (<div style={{padding:20}}><h2>HITL UI Demo</h2><div>Logs:</div><pre>{logs.join('\n\n')}</pre></div>)
}
export default App;
