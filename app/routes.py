import json, os, uuid
from flask import Blueprint, Response, current_app, jsonify, render_template, request, stream_with_context
from .database import get_db
from .agent import stream_agent

bp = Blueprint("main", __name__)

def owner():
    value = request.headers.get("X-Owner-ID") or request.args.get("owner_id") or "local-user"
    return value[:80]

@bp.get("/")
def index():
    return render_template("index.html", default_model=os.getenv("GROQ_MODEL","openai/gpt-oss-20b"))

@bp.get("/api/status")
def status():
    key = bool(os.getenv("GROQ_API_KEY","").strip() and os.getenv("GROQ_API_KEY") != "sua_chave_groq_aqui")
    return jsonify({"configured":key,"default_model":os.getenv("GROQ_MODEL","openai/gpt-oss-20b")})

@bp.get("/api/conversations")
def conversations():
    rows = get_db().execute("""SELECT id,title,created_at,updated_at FROM conversations
      WHERE owner_id=? ORDER BY updated_at DESC""",(owner(),)).fetchall()
    return jsonify([dict(r) for r in rows])

@bp.post("/api/conversations")
def new_conversation():
    data = request.get_json(silent=True) or {}
    cid = str(uuid.uuid4())
    title = str(data.get("title","Nova conversa"))[:100]
    get_db().execute("INSERT INTO conversations(id,owner_id,title) VALUES(?,?,?)",(cid,owner(),title))
    get_db().commit()
    return jsonify({"id":cid,"title":title})

@bp.get("/api/conversations/<cid>/messages")
def get_messages(cid):
    db = get_db()
    exists = db.execute("SELECT 1 FROM conversations WHERE id=? AND owner_id=?",(cid,owner())).fetchone()
    if not exists: return jsonify({"error":"Conversa não encontrada."}),404
    rows = db.execute("SELECT role,content,created_at FROM messages WHERE conversation_id=? ORDER BY id",(cid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@bp.delete("/api/conversations/<cid>")
def delete_conversation(cid):
    db = get_db()
    cur = db.execute("DELETE FROM conversations WHERE id=? AND owner_id=?",(cid,owner()))
    db.commit()
    return (jsonify({"deleted":True}) if cur.rowcount else (jsonify({"error":"Não encontrada"}),404))

@bp.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    cid = str(data.get("conversation_id",""))
    prompt = str(data.get("message","")).strip()
    model = str(data.get("model",os.getenv("GROQ_MODEL","openai/gpt-oss-20b")))[:100]
    if not prompt: return jsonify({"error":"Digite uma mensagem."}),400
    if len(prompt) > 12000: return jsonify({"error":"Mensagem muito longa (limite de 12.000 caracteres)."}),400
    db = get_db()
    conv = db.execute("SELECT id FROM conversations WHERE id=? AND owner_id=?",(cid,owner())).fetchone()
    if not conv: return jsonify({"error":"Crie ou selecione uma conversa."}),404
    count = db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=?",(cid,)).fetchone()[0]
    if count == 0:
        title = prompt[:48] + ("…" if len(prompt)>48 else "")
        db.execute("UPDATE conversations SET title=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(title,cid))
    db.execute("INSERT INTO messages(conversation_id,role,content) VALUES(?,?,?)",(cid,"user",prompt))
    db.execute("UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?",(cid,))
    db.commit()

    @stream_with_context
    def generate():
        try:
            for event in stream_agent(owner(),cid,model):
                yield "data: "+json.dumps(event,ensure_ascii=False)+"\n\n"
        except Exception as exc:
            # Não expor detalhes internos/credenciais da API ao navegador.
            message = str(exc)
            if "authentication" in message.lower() or "api_key" in message.lower():
                message = "A Groq recusou a chave. Confira GROQ_API_KEY no arquivo .env."
            elif "model" in message.lower() and ("not found" in message.lower() or "decommission" in message.lower()):
                message = "O modelo selecionado não está disponível. Escolha outro modelo na lista."
            else:
                message = "Não foi possível concluir a resposta. Confira a chave, o modelo e sua conexão."
            yield "data: "+json.dumps({"type":"error","message":message},ensure_ascii=False)+"\n\n"
    return Response(generate(),mimetype="text/event-stream",headers={
        "Cache-Control":"no-cache","X-Accel-Buffering":"no"
    })

@bp.get("/api/memories")
def memories():
    rows = get_db().execute("SELECT id,memory_key,memory_value,updated_at FROM memories WHERE owner_id=? ORDER BY updated_at DESC",(owner(),)).fetchall()
    return jsonify([dict(r) for r in rows])

@bp.delete("/api/memories/<int:mid>")
def delete_memory(mid):
    cur = get_db().execute("DELETE FROM memories WHERE id=? AND owner_id=?",(mid,owner()))
    get_db().commit()
    return (jsonify({"deleted":True}) if cur.rowcount else (jsonify({"error":"Não encontrada"}),404))

@bp.get("/api/tasks")
def tasks():
    rows = get_db().execute("SELECT id,title,done,created_at FROM tasks WHERE owner_id=? ORDER BY id DESC",(owner(),)).fetchall()
    return jsonify([dict(r) for r in rows])
