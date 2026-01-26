import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.application.rag_agent import RAGAgent

class TestRAGAgentManual(unittest.TestCase):
    
    @patch('src.application.rag_agent.SQLDatabase')
    @patch('src.application.rag_agent.OllamaLLM')
    @patch('src.application.rag_agent.OllamaClient')
    def test_get_answer_workflow(self, mock_client_cls, mock_llm_cls, mock_db_cls):
        # Setup Mocks
        mock_db = MagicMock()
        mock_db_cls.from_uri.return_value = mock_db
        mock_db.get_table_info.return_value = "SCHEMA_INFO"
        
        mock_llm = MagicMock()
        mock_llm_cls.return_value = mock_llm
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.is_available.return_value = True
        
        # Instantiate Agent
        agent = RAGAgent()
        
        # --- TEST CHANGE 1: Empty Result from DB ---
        # Mock LLM generating SQL
        mock_llm.invoke.side_effect = [
            "```sql\nSELECT * FROM table\n```", # 1st call: Generate SQL
             # Expect NO 2nd call to LLM if DB returns empty
        ]
        
        # Mock DB execution returning empty string
        mock_db.run.return_value = "" 
        
        result = agent.get_answer("Pregunta vacia")
        
        print("\n--- TEST 1: Empty DB Result ---")
        print(f"Result: {result}")
        
        self.assertIn("No encontré información", result['answer'])
        self.assertEqual(result['raw_data'], "") # Raw string from DB is empty
        # Actually in the code: if not db_result... result_package["answer"] = ...
        # logic: if not db_result or db_result == "" ...
        
        # --- TEST CASE 2: Valid Result from DB ---
        
        # Reset side effects
        mock_llm.invoke.side_effect = [
            "SELECT * FROM farmacia",   # 1st call: SQL
            "La farmacia está en el piso 1." # 2nd call: Final Answer
        ]
        
        mock_db.run.return_value = "[('Farmacia', 'Piso 1')]"
        
        result2 = agent.get_answer("Donde esta la farmacia")
        
        print("\n--- TEST 2: Valid DB Result ---")
        print(f"Result: {result2}")
        
        self.assertEqual(result2['sql'], "SELECT * FROM farmacia")
        self.assertEqual(result2['raw_data'], "[('Farmacia', 'Piso 1')]")
        self.assertEqual(result2['answer'], "La farmacia está en el piso 1.")
        
        # Verify calls
        # 1. get_table_info (called twice, once per test/instantiation? No, instantiated once)
        # We reused 'agent' but 'invoke' side_effect is continuous.
        
if __name__ == '__main__':
    unittest.main()
