from datetime import datetime
from zoneinfo import ZoneInfo
from .database import get_db
from .calculator import safe_calculate

def tool_definitions():
    return [
      {"type":"function","function":{"name":"calculator","description":"Calcula uma expressão aritmética simples.","parameters":{"type":"object","properties":{"expression":{"type":"string","description":"Ex.: (25 * 4) / 2"}},"required":["expression"]}}},
      {"type":"function","function":{"name":"current_datetime","description":"Retorna data e hora atuais de São Paulo.","parameters":{"type":"object","properties":{},"required":[]}}},
      {"type":"function","function":{"name":"save_memory","description":"Salva uma informação que o usuário pediu explicitamente para lembrar.","parameters":{"type":"object","properties":{"key":{"type":"string"},"value":{"type":"string"}},"required":["key","value"]}}},
      {"type":"function","function":{"name":"recall_memories","description":"Consulta informações salvas na memória de longo prazo.","parameters":{"type":"object","properties":{"query":{"type":"string","description":"Palavra ou assunto para procurar"}},"required":["query"]}}},
      {"type":"function","function":{"name":"create_task","description":"Cria uma tarefa na lista do usuário.","parameters":{"type":"object","properties":{"title":{"type":"string"}},"required":["title"]}}},
      {"type":"function","function":{"name":"list_tasks","description":"Lista as tarefas do usuário.","parameters":{"type":"object","properties":{"include_completed":{"type":"boolean"}},"required":[]}}},
      {"type":"function","function":{"name":"complete_task","description":"Marca uma tarefa como concluída pelo identificador.","parameters":{"type":"object","properties":{"task_id":{"type":"integer"}},"required":["task_id"]}}}
    ]

def execute_tool(name, args, owner_id):
    db = get_db()
    if name == "calculator":
        return {"result": safe_calculate(args["expression"])}
    if name == "current_datetime":
        now = datetime.now(ZoneInfo("America/Sao_Paulo"))
        return {"datetime": now.strftime("%d/%m/%Y %H:%M:%S"), "timezone":"America/Sao_Paulo"}
    if name == "save_memory":
        key, value = str(args["key"]).strip()[:80], str(args["value"]).strip()[:1000]
        if not key or not value:
            raise ValueError("Chave e informação não podem ficar vazias.")
        db.execute("""INSERT INTO memories(owner_id,memory_key,memory_value)
          VALUES(?,?,?) ON CONFLICT(owner_id,memory_key) DO UPDATE SET
          memory_value=excluded.memory_value, updated_at=CURRENT_TIMESTAMP""",
          (owner_id,key,value))
        db.commit()
        return {"saved":True,"key":key}
    if name == "recall_memories":
        q = f"%{str(args.get('query',''))[:80]}%"
        rows = db.execute("""SELECT memory_key,memory_value FROM memories
          WHERE owner_id=? AND (memory_key LIKE ? OR memory_value LIKE ?)
          ORDER BY updated_at DESC LIMIT 12""",(owner_id,q,q)).fetchall()
        return {"memories":[dict(r) for r in rows]}
    if name == "create_task":
        title = str(args["title"]).strip()[:180]
        if not title:
            raise ValueError("A tarefa precisa de um título.")
        cur = db.execute("INSERT INTO tasks(owner_id,title) VALUES(?,?)",(owner_id,title))
        db.commit()
        return {"created":True,"task_id":cur.lastrowid,"title":title}
    if name == "list_tasks":
        include = bool(args.get("include_completed",False))
        sql = "SELECT id,title,done,created_at FROM tasks WHERE owner_id=?"
        if not include:
            sql += " AND done=0"
        rows = db.execute(sql+" ORDER BY id DESC LIMIT 50",(owner_id,)).fetchall()
        return {"tasks":[dict(r) for r in rows]}
    if name == "complete_task":
        task_id = int(args["task_id"])
        cur = db.execute("UPDATE tasks SET done=1 WHERE id=? AND owner_id=?",(task_id,owner_id))
        db.commit()
        if not cur.rowcount:
            return {"completed":False,"message":"Tarefa não encontrada."}
        return {"completed":True,"task_id":task_id}
    raise ValueError("Ferramenta não autorizada.")
