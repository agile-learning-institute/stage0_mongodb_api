import unittest
from unittest.mock import patch, MagicMock
from stage0_fran.services.chain_services import ChainServices

class TestChainServices(unittest.TestCase):

    @patch('stage0_fran.services.chain_services.MongoIO.get_instance')
    @patch('stage0_fran.services.chain_services.Config.get_instance')
    def test_get_chains(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.get_documents.return_value = [{"_id": "chain1", "name": "Test Chain"}]

        token = {"user_id": "test_user"}
        result = ChainServices.get_chains(token)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Test Chain")
        mock_mongo_instance.get_documents.assert_called_once()

    @patch('stage0_fran.services.chain_services.MongoIO.get_instance')
    @patch('stage0_fran.services.chain_services.Config.get_instance')
    def test_get_chain(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.get_document.return_value = {"_id": "chain1", "name": "Test Chain"}

        token = {"user_id": "test_user"}
        result = ChainServices.get_chain("chain1", token)

        self.assertEqual(result["_id"], "chain1")
        self.assertEqual(result["name"], "Test Chain")
        mock_mongo_instance.get_document.assert_called_once()

if __name__ == '__main__':
    unittest.main()
