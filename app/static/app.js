const $ = (id) => document.getElementById(id);
const ownerId = localStorage.getItem("indu_owner_id") || crypto.randomUUID();
localStorage.setItem("indu_owner_id", ownerId);
let currentConversation = null, busy = false;
const headers = {"Content-Type":"application/json","X-Owner-ID":ownerId};
const messagesEl = $("messages"), input = $("messageInput");

async function api(url, options={}) {
  const response = await fetch(url,{...options,headers:{...headers,...(options.headers||{})}});
  const data = await response.json().catch(()=>({}));
  if(!response.ok) throw new Error(data.error || "Erro na solicitação.");
  return data;
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function renderMarkdown(text){
  const html = window.marked ? marked.parse(text) : `<p>${escapeHtml(text)}</p>`;
  return window.DOMPurify ? DOMPurify.sanitize(html) : html;
}
function scrollBottom(){ $("chatArea").scrollTop=$("chatArea").scrollHeight; }
function addMessage(role,content="",typing=false){
  $("welcome").style.display="none";
  const row=document.createElement("div"); row.className=`message ${role}`;
  const avatar=document.createElement("div");avatar.className="message-avatar";avatar.textContent=role==="user"?"Você":"✳";
  const bubble=document.createElement("div");bubble.className="bubble";
  if(typing){bubble.innerHTML='<div class="typing"><i></i><i></i><i></i></div>';}
  else bubble.innerHTML=role==="assistant"?renderMarkdown(content):escapeHtml(content).replace(/\n/g,"<br>");
  row.append(avatar,bubble);messagesEl.append(row);scrollBottom();
  return {row,bubble};
}
async function loadConversations(){
  const list=$("conversationList");list.innerHTML="";
  const items=await api("/api/conversations");
  items.forEach(c=>{
    const el=document.createElement("div");el.className="conv-item"+(c.id===currentConversation?" active":"");
    el.innerHTML=`<span>◷</span><span>${escapeHtml(c.title)}</span>`;
    el.onclick=()=>openConversation(c.id);list.append(el);
  });
}
async function createConversation(){
  const c=await api("/api/conversations",{method:"POST",body:JSON.stringify({})});
  currentConversation=c.id;messagesEl.innerHTML="";$("welcome").style.display="block";await loadConversations();return c.id;
}
async function openConversation(id){
  currentConversation=id;messagesEl.innerHTML="";$("welcome").style.display="none";
  const list=await api(`/api/conversations/${id}/messages`);
  if(!list.length)$("welcome").style.display="block";
  list.forEach(m=>addMessage(m.role,m.content));await loadConversations();
  $("sidebar").classList.remove("open");
}
async function sendMessage(text){
  if(busy||!text.trim())return;
  if(!currentConversation)await createConversation();
  busy=true;$("sendButton").disabled=true;input.value="";resizeInput();
  addMessage("user",text);
  const assistant=addMessage("assistant","",true);
  try{
    const response=await fetch("/api/chat",{method:"POST",headers:headers,body:JSON.stringify({
      conversation_id:currentConversation,message:text,model:$("modelSelect").value
    })});
    if(!response.ok){const err=await response.json();throw new Error(err.error||"Falha ao conversar.");}
    const reader=response.body.getReader(),decoder=new TextDecoder();let buffer="",answer="";
    while(true){
      const {value,done}=await reader.read();if(done)break;
      buffer+=decoder.decode(value,{stream:true});
      const events=buffer.split("\n\n");buffer=events.pop();
      for(const event of events){
        const line=event.split("\n").find(x=>x.startsWith("data: "));if(!line)continue;
        const data=JSON.parse(line.slice(6));
        if(data.type==="delta"){answer+=data.content;assistant.bubble.innerHTML=renderMarkdown(answer);scrollBottom();}
        if(data.type==="status"){assistant.bubble.dataset.status=data.message;}
        if(data.type==="error"){throw new Error(data.message);}
      }
    }
    if(!answer)assistant.bubble.innerHTML=renderMarkdown("Não recebi conteúdo do modelo. Tente novamente.");
  }catch(err){assistant.bubble.innerHTML=`<p class="error-text">${escapeHtml(err.message)}</p>`;}
  finally{busy=false;$("sendButton").disabled=false;input.focus();await loadConversations();}
}
function resizeInput(){input.style.height="auto";input.style.height=Math.min(input.scrollHeight,180)+"px";}
input.addEventListener("input",resizeInput);
input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendMessage(input.value);}});
$("sendButton").onclick=()=>sendMessage(input.value);
$("newChat").onclick=async()=>{if(busy)return;await createConversation();};
document.querySelectorAll("[data-prompt]").forEach(b=>b.onclick=()=>sendMessage(b.dataset.prompt));
$("mobileMenu").onclick=()=>$("sidebar").classList.toggle("open");
$("themeToggle").onclick=()=>document.body.classList.toggle("light");
$("closeModal").onclick=()=>$("modalBackdrop").classList.remove("open");
$("modalBackdrop").onclick=e=>{if(e.target===$("modalBackdrop"))$("modalBackdrop").classList.remove("open");};

async function openPanel(kind){
  $("modalTitle").textContent=kind==="memory"?"Memórias de longo prazo":"Minhas tarefas";
  $("modalContent").innerHTML='<div class="empty">Carregando…</div>';$("modalBackdrop").classList.add("open");
  try{
    const data=await api(kind==="memory"?"/api/memories":"/api/tasks");
    if(!data.length){$("modalContent").innerHTML='<div class="empty">Nada por aqui ainda. Converse com a IA para criar memórias ou tarefas.</div>';return;}
    $("modalContent").innerHTML=data.map(item=>kind==="memory"
      ?`<div class="data-row"><button class="delete-btn" data-delete-memory="${item.id}">Excluir</button><b>${escapeHtml(item.memory_key)}</b><small>${escapeHtml(item.memory_value)}</small></div>`
      :`<div class="data-row"><b>#${item.id} · ${escapeHtml(item.title)}</b><small>${item.done?"Concluída":"Pendente"} · ${escapeHtml(item.created_at)}</small></div>`).join("");
    document.querySelectorAll("[data-delete-memory]").forEach(btn=>btn.onclick=async()=>{await api("/api/memories/"+btn.dataset.deleteMemory,{method:"DELETE"});openPanel("memory");});
  }catch(e){$("modalContent").textContent=e.message;}
}
$("memoryButton").onclick=()=>openPanel("memory");
$("taskButton").onclick=()=>openPanel("tasks");
async function init(){
  $("modelSelect").value=window.DEFAULT_MODEL;
  try{
    const status=await api("/api/status");
    $("apiStatus").textContent=status.configured?"API Groq conectada":"Configure sua chave Groq";
    $("apiPulse").classList.toggle("ok",status.configured);
  }catch{$("apiStatus").textContent="Servidor indisponível";}
  await loadConversations();
  const convs=await api("/api/conversations");
  if(convs.length)await openConversation(convs[0].id);else await createConversation();
}
init().catch(e=>console.error(e));
