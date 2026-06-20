try:
    from app.agents.base import BaseAgent
    print("✅ BaseAgent imported successfully")
except Exception as e:
    print(f"❌ BaseAgent import failed: {e}")

try:
    from app.agents.radar import RadarAgent
    print("✅ RadarAgent imported successfully")
except Exception as e:
    print(f"❌ RadarAgent import failed: {e}")

try:
    from app.agents.vault import VaultAgent
    print("✅ VaultAgent imported successfully")
except Exception as e:
    print(f"❌ VaultAgent import failed: {e}")

try:
    from app.agents.reasoning import ReasoningAgent
    print("✅ ReasoningAgent imported successfully")
except Exception as e:
    print(f"❌ ReasoningAgent import failed: {e}")

try:
    from app.orchestrator import Orchestrator
    print("✅ Orchestrator imported successfully")
except Exception as e:
    print(f"❌ Orchestrator import failed: {e}")

try:
    from app.api.v1.intelligence import router as intelligence_router
    print("✅ Intelligence router imported successfully")
except Exception as e:
    print(f"❌ Intelligence router import failed: {e}")
