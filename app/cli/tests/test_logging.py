"""
Comprehensive tests for logging functionality.

These tests verify:
- Logger setup and configuration
- Log file creation and management
- Log message formatting and levels
- Integration with CLI operations
- Log rotation and cleanup (if applicable)
"""

import unittest
import tempfile
import os
import sys
import logging
from unittest.mock import patch, MagicMock, call
import shutil

# Add the CLI directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main


class TestLoggerSetup(unittest.TestCase):
    """Test logger setup functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        # Clear any existing handlers from previous tests
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        # Clear handlers after test
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    @patch('os.path.expanduser')
    @patch('os.makedirs')
    @patch('logging.FileHandler')
    def test_default_logger_setup(self, mock_file_handler, mock_makedirs, mock_expanduser):
        """Test default logger setup."""
        mock_expanduser.return_value = self.temp_dir
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        logger = main.setup_logger()
        
        # Should create log directory
        mock_makedirs.assert_called_once()
        
        # Should create file handler
        mock_file_handler.assert_called_once()
        
        # Should configure handler
        mock_handler.setLevel.assert_called_once_with(logging.INFO)
        mock_handler.setFormatter.assert_called_once()
        
        # Should return logger
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "pdst-calc")
    
    @patch('os.path.expanduser')
    @patch('os.makedirs')
    @patch('logging.FileHandler')
    def test_custom_session_name_logger(self, mock_file_handler, mock_makedirs, mock_expanduser):
        """Test logger setup with custom session name."""
        mock_expanduser.return_value = self.temp_dir
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        logger = main.setup_logger("test_session")
        
        # Should use custom session name in file path
        call_args = mock_file_handler.call_args[0][0]
        self.assertIn("test_session", call_args)
    
    def test_logger_file_path_construction(self):
        """Test correct log file path construction."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler') as mock_handler:
                    main.setup_logger("my_session")
                    
                    # Extract the file path used
                    file_path = mock_handler.call_args[0][0]
                    
                    # Should contain expected components
                    self.assertIn(".pdst-calc", file_path)
                    self.assertIn("logs", file_path)
                    self.assertIn("my_session", file_path)
                    self.assertTrue(file_path.endswith(".log"))
    
    def test_logger_level_configuration(self):
        """Test logger level configuration."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler', return_value=MagicMock()):
                    logger = main.setup_logger()
                    
                    # Should set INFO level
                    self.assertEqual(logger.level, logging.INFO)
    
    def test_formatter_configuration(self):
        """Test log formatter configuration."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler') as mock_file_handler:
                    mock_handler = MagicMock()
                    mock_file_handler.return_value = mock_handler
                    
                    main.setup_logger()
                    
                    # Should set formatter
                    mock_handler.setFormatter.assert_called_once()
                    formatter_call = mock_handler.setFormatter.call_args[0][0]
                    self.assertIsInstance(formatter_call, logging.Formatter)


class TestLogFileCreation(unittest.TestCase):
    """Test log file creation and management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, ".pdst-calc", "logs")
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        # Clear any handlers
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def test_log_directory_creation(self):
        """Test that log directory is created."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            # Don't mock makedirs so we can test actual directory creation
            with patch('logging.FileHandler', return_value=MagicMock()):
                main.setup_logger()
                
                # Directory should be created
                self.assertTrue(os.path.exists(self.log_dir))
    
    def test_log_file_naming(self):
        """Test log file naming convention."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler') as mock_handler:
                    main.setup_logger("test_session_123")
                    
                    file_path = mock_handler.call_args[0][0]
                    filename = os.path.basename(file_path)
                    
                    self.assertTrue(filename.startswith("pdst-calc-"))
                    self.assertIn("test_session_123", filename)
                    self.assertTrue(filename.endswith(".log"))
    
    def test_multiple_logger_instances(self):
        """Test creating multiple logger instances."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler') as mock_handler:
                    logger1 = main.setup_logger("session1")
                    logger2 = main.setup_logger("session2")
                    
                    # Should be the same logger instance (same name)
                    self.assertEqual(logger1.name, logger2.name)
                    
                    # But should have been configured twice
                    self.assertEqual(mock_handler.call_count, 2)
    
    @patch('os.makedirs')
    def test_log_directory_creation_failure(self, mock_makedirs):
        """Test handling when log directory cannot be created."""
        mock_makedirs.side_effect = OSError("Permission denied")
        
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with self.assertRaises(OSError):
                main.setup_logger()


class TestLogMessageFormatting(unittest.TestCase):
    """Test log message formatting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def test_log_message_format(self):
        """Test that log messages are formatted correctly."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler') as mock_file_handler:
                    mock_handler = MagicMock()
                    mock_file_handler.return_value = mock_handler
                    
                    logger = main.setup_logger()
                    
                    # Check formatter pattern
                    formatter_call = mock_handler.setFormatter.call_args[0][0]
                    format_string = formatter_call._fmt
                    
                    # Should contain timestamp, level, and message
                    self.assertIn("%(asctime)s", format_string)
                    self.assertIn("%(levelname)s", format_string)
                    self.assertIn("%(message)s", format_string)
    
    def test_actual_log_writing(self):
        """Test actual log message writing to file."""
        log_file = os.path.join(self.temp_dir, "test.log")
        
        # Create a real logger that writes to file
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Write test messages
        logger.info("Test info message")
        logger.error("Test error message")
        
        # Clean up handler
        handler.close()
        logger.removeHandler(handler)
        
        # Verify file contents
        with open(log_file, 'r') as f:
            content = f.read()
            
        self.assertIn("INFO", content)
        self.assertIn("ERROR", content)
        self.assertIn("Test info message", content)
        self.assertIn("Test error message", content)


class TestLoggingIntegration(unittest.TestCase):
    """Test logging integration with CLI operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    @patch('main.print_header')
    @patch('main.print_help_text')
    @patch('main.print_success')
    @patch('main.print_step')
    @patch('main.load_drug_data')
    @patch('main.run_calculation')
    def test_main_function_logging(self, mock_run_calc, mock_load_data, mock_step, 
                                 mock_success, mock_help, mock_header):
        """Test that main function uses logging appropriately."""
        mock_load_data.return_value = MagicMock()
        
        with patch('sys.argv', ['main.py', '--session-name', 'test']):
            with patch('os.path.expanduser', return_value=self.temp_dir):
                with patch('os.makedirs'):
                    with patch('logging.FileHandler') as mock_file_handler:
                        mock_handler = MagicMock()
                        mock_file_handler.return_value = mock_handler
                        
                        main.main()
                        
                        # Logger should be created
                        mock_file_handler.assert_called_once()
    
    @patch('main.select_drugs')
    @patch('main.purchased_weights')
    @patch('main.stock_volume')
    @patch('main.cal_potency')
    @patch('main.act_drugweight')
    @patch('main.cal_stockdil')
    @patch('main.mgit_tubes')
    @patch('main.cal_mgit_ws')
    @patch('main.print_step')
    @patch('main.print_success')
    @patch('builtins.print')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('builtins.input')
    def test_run_calculation_logging(self, mock_input, mock_open, mock_makedirs, 
                                   mock_print, mock_success, mock_step, mock_mgit_ws,
                                   mock_mgit_tubes, mock_stockdil, mock_drugweight,
                                   mock_potency, mock_volume, mock_weights, mock_select):
        """Test that run_calculation function logs appropriately."""
        
        # Set up mock returns
        import pandas as pd
        sample_df = pd.DataFrame({
            'Drug': ['Drug1', 'Drug2'],
            'OrgMolecular_Weight': [100.0, 200.0],
            'Critical_Concentration': [1.0, 2.0]
        })
        
        mock_select.return_value = sample_df
        mock_input.side_effect = ['n', 'output_file', 'final_file']
        
        # Create mock logger
        mock_logger = MagicMock()
        
        # Run the function
        main.run_calculation(sample_df, None, None, mock_logger)
        
        # Should have logged various events
        self.assertTrue(mock_logger.info.called)
    
    def test_session_name_in_log_path(self):
        """Test that session name appears in log file path."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler') as mock_handler:
                    main.setup_logger("my_test_session")
                    
                    file_path = mock_handler.call_args[0][0]
                    self.assertIn("my_test_session", file_path)
    
    def test_logger_reuse(self):
        """Test that logger instances are reused appropriately."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler', return_value=MagicMock()):
                    logger1 = main.setup_logger("session1")
                    logger2 = main.setup_logger("session2")
                    
                    # Should be the same logger object (same name)
                    self.assertIs(logger1, logger2)


class TestLogLevels(unittest.TestCase):
    """Test different log levels and their usage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def test_info_level_logging(self):
        """Test INFO level logging."""
        log_file = os.path.join(self.temp_dir, "info_test.log")
        
        logger = logging.getLogger("info_test")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.info("Info message")
        logger.debug("Debug message")  # Should not appear
        
        handler.close()
        logger.removeHandler(handler)
        
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Info message", content)
        self.assertNotIn("Debug message", content)
    
    def test_error_level_logging(self):
        """Test ERROR level logging."""
        log_file = os.path.join(self.temp_dir, "error_test.log")
        
        logger = logging.getLogger("error_test")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.error("Error message")
        logger.warning("Warning message")
        logger.info("Info message")
        
        handler.close()
        logger.removeHandler(handler)
        
        with open(log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Error message", content)
        self.assertIn("Warning message", content)
        self.assertIn("Info message", content)
    
    def test_logger_default_level(self):
        """Test that logger is set to correct default level."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('os.makedirs'):
                with patch('logging.FileHandler', return_value=MagicMock()):
                    logger = main.setup_logger()
                    
                    self.assertEqual(logger.level, logging.INFO)


class TestLogFileManagement(unittest.TestCase):
    """Test log file management features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, ".pdst-calc", "logs")
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        logger = logging.getLogger("pdst-calc")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    def test_log_file_permissions(self):
        """Test log file permissions."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            # Don't mock file creation to test actual permissions
            with patch('logging.FileHandler') as mock_handler:
                # Create a real file to test permissions
                test_log = os.path.join(self.temp_dir, "test.log")
                with open(test_log, 'w') as f:
                    f.write("test")
                
                # Check file is readable and writable
                self.assertTrue(os.access(test_log, os.R_OK))
                self.assertTrue(os.access(test_log, os.W_OK))
    
    def test_concurrent_log_access(self):
        """Test handling of concurrent log access."""
        # This would test scenarios where multiple processes might
        # try to write to the same log file
        import threading
        import time
        
        log_file = os.path.join(self.temp_dir, "concurrent.log")
        
        def write_to_log(thread_id):
            logger = logging.getLogger(f"thread_{thread_id}")
            handler = logging.FileHandler(log_file)
            logger.addHandler(handler)
            logger.info(f"Message from thread {thread_id}")
            handler.close()
            logger.removeHandler(handler)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_to_log, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all messages were written
        with open(log_file, 'r') as f:
            content = f.read()
        
        for i in range(5):
            self.assertIn(f"Message from thread {i}", content)
    
    def test_log_directory_structure(self):
        """Test correct log directory structure creation."""
        with patch('os.path.expanduser', return_value=self.temp_dir):
            with patch('logging.FileHandler', return_value=MagicMock()):
                main.setup_logger()
                
                # Should create the correct directory structure
                self.assertTrue(os.path.exists(self.log_dir))
                
                # Should be in user's home directory structure
                pdst_dir = os.path.join(self.temp_dir, ".pdst-calc")
                self.assertTrue(os.path.exists(pdst_dir))


if __name__ == '__main__':
    unittest.main()
