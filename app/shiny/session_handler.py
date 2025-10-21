"""
Session management module for the DST Calculator Shiny app.
Handles all session-related operations including:
- Session data structures
- Save/Load operations
- Data validation and conversion
- Session state management
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionHandler:
    """Handles session management for DST Calculator application."""
    
    def __init__(self, db_manager):
        """Initialize session handler with database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db_manager = db_manager
        
    def extract_current_inputs(self, selected_drugs: List[str], input_obj, 
                             volume_unit: str, weight_unit: str, make_stock: bool) -> Dict[str, Any]:
        """Extract current user inputs from the Shiny input object.
        
        Args:
            selected_drugs: List of selected drug names
            input_obj: Shiny input object containing user inputs
            volume_unit: Current volume unit setting
            weight_unit: Current weight unit setting
            make_stock: Whether making stock solutions
            
        Returns:
            Dictionary containing extracted input data
        """
        try:
            # Create inputs dictionary for each drug
            drug_inputs = {}
            
            for i, drug_name in enumerate(selected_drugs):
                try:
                    # Extract Step 2 inputs (parameters)
                    custom_crit = getattr(input_obj, f'custom_crit_{i}', lambda: None)()
                    purch_molw = getattr(input_obj, f'purch_molw_{i}', lambda: None)()
                    stock_vol = getattr(input_obj, f'stock_vol_{i}', lambda: None)() if make_stock else None
                    mgit_tubes = getattr(input_obj, f'mgit_tubes_{i}', lambda: None)()
                    
                    # Extract aliquot inputs (if making stock)
                    num_aliquots = None
                    ml_per_aliquot = None
                    if make_stock:
                        num_aliquots = getattr(input_obj, f'num_aliquots_{i}', lambda: None)()
                        ml_per_aliquot = getattr(input_obj, f'ml_per_aliquot_{i}', lambda: None)()
                    
                    # Extract Step 3 inputs (actual weights)
                    actual_weight = getattr(input_obj, f'actual_weight_{i}', lambda: None)()
                    
                    # Store in structured format
                    drug_inputs[str(i)] = {
                        'drug_name': drug_name,
                        'custom_crit_conc': custom_crit,
                        'purchased_molw': purch_molw,
                        'stock_volume': stock_vol,
                        'mgit_tubes': mgit_tubes,
                        'num_aliquots': num_aliquots,
                        'ml_per_aliquot': ml_per_aliquot,
                        'actual_weight': actual_weight
                    }
                    
                    logger.debug(f"Extracted inputs for drug {i} ({drug_name}): {drug_inputs[str(i)]}")
                    
                except Exception as e:
                    logger.warning(f"Failed to extract inputs for drug {i} ({drug_name}): {e}")
                    continue
            
            return {
                'selected_drugs': selected_drugs,
                'drug_inputs': drug_inputs,
                'volume_unit': volume_unit,
                'weight_unit': weight_unit,
                'make_stock': make_stock,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to extract current inputs: {e}")
            return {}
    
    def save_session_step2(self, session_id: int, selected_drugs: List[str], 
                          input_obj, volume_unit: str, weight_unit: str, 
                          make_stock: bool) -> bool:
        """Save session data after Step 2 (parameter entry).
        
        Args:
            session_id: Session ID to update
            selected_drugs: List of selected drug names
            input_obj: Shiny input object
            volume_unit: Current volume unit
            weight_unit: Current weight unit
            make_stock: Whether making stock solutions
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Extract current inputs
            inputs_data = self.extract_current_inputs(
                selected_drugs, input_obj, volume_unit, weight_unit, make_stock
            )
            
            if not inputs_data:
                logger.error("Failed to extract inputs data for Step 2 save")
                return False
            
            # Create session preparation data
            preparation_data = {
                'session_name': f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'step': 2,
                'completed_steps': [1, 2],
                'inputs': inputs_data,
                'calculations': {},
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to database
            success = self.db_manager.update_session_data(session_id, preparation_data)
            
            if success:
                logger.info(f"Session {session_id} saved successfully at Step 2")
            else:
                logger.error(f"Failed to save session {session_id} at Step 2")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving session {session_id} at Step 2: {e}")
            return False
    
    def save_session_step3(self, session_id: int, selected_drugs: List[str],
                          input_obj, volume_unit: str, weight_unit: str,
                          make_stock: bool, calculation_results: Dict[str, Any]) -> bool:
        """Save session data after Step 3 (final calculations).
        
        Args:
            session_id: Session ID to update
            selected_drugs: List of selected drug names  
            input_obj: Shiny input object
            volume_unit: Current volume unit
            weight_unit: Current weight unit
            make_stock: Whether making stock solutions
            calculation_results: Results from perform_final_calculations()
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Extract current inputs (including actual weights from Step 3)
            inputs_data = self.extract_current_inputs(
                selected_drugs, input_obj, volume_unit, weight_unit, make_stock
            )
            
            if not inputs_data:
                logger.error("Failed to extract inputs data for Step 3 save")
                return False
            
            # Create session preparation data
            preparation_data = {
                'session_name': f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'step': 3,
                'completed_steps': [1, 2, 3],
                'inputs': inputs_data,
                'calculations': {
                    'final_results': calculation_results,
                    'calculated_at': datetime.now().isoformat()
                },
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to database
            success = self.db_manager.update_session_data(session_id, preparation_data)
            
            if success:
                logger.info(f"Session {session_id} saved successfully at Step 3 with calculations")
            else:
                logger.error(f"Failed to save session {session_id} at Step 3")
                
            return success
            
        except Exception as e:
            logger.error(f"Error saving session {session_id} at Step 3: {e}")
            return False
    
    def load_session_data(self, session_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Load session data from database.
        
        Args:
            session_id: Session ID to load
            user_id: User ID for security check
            
        Returns:
            Session data dictionary or None if not found/error
        """
        try:
            with self.db_manager.get_connection() as conn:
                cur = conn.execute(
                    "SELECT preparation, session_name, session_date FROM session WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id)
                )
                row = cur.fetchone()
                
            if not row or not row[0]:
                logger.warning(f"No session data found for session {session_id}, user {user_id}")
                return None
                
            preparation_data = json.loads(row[0])
            preparation_data['session_name'] = row[1]
            preparation_data['session_date'] = row[2]
            
            logger.info(f"Loaded session {session_id} for user {user_id}")
            return preparation_data
            
        except Exception as e:
            logger.error(f"Error loading session {session_id} for user {user_id}: {e}")
            return None
    
    def restore_inputs_from_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert session data to input format compatible with current app structure.
        
        Args:
            session_data: Session data from database
            
        Returns:
            Dictionary with inputs in format expected by get_drug_inputs()
        """
        try:
            inputs_data = session_data.get('inputs', {})
            drug_inputs = inputs_data.get('drug_inputs', {})
            selected_drugs = inputs_data.get('selected_drugs', [])
            
            # Convert to format expected by app
            restored_inputs = {}
            
            for i, drug_name in enumerate(selected_drugs):
                drug_data = drug_inputs.get(str(i), {})
                
                # Map session data to current input structure
                restored_inputs[i] = {
                    'custom_crit': drug_data.get('custom_crit_conc'),
                    'purch_molw': drug_data.get('purchased_molw'),
                    'stock_vol': drug_data.get('stock_volume'),
                    'mgit_tubes': drug_data.get('mgit_tubes'),
                    'num_aliquots': drug_data.get('num_aliquots'),
                    'ml_per_aliquot': drug_data.get('ml_per_aliquot'),
                    'actual_weight': drug_data.get('actual_weight')
                }
            
            # Also include session-level settings
            restored_inputs['session_settings'] = {
                'selected_drugs': selected_drugs,
                'volume_unit': inputs_data.get('volume_unit', 'ml'),
                'weight_unit': inputs_data.get('weight_unit', 'mg'),
                'make_stock': inputs_data.get('make_stock', True),
                'step': session_data.get('step', 1),
                'completed_steps': session_data.get('completed_steps', [])
            }
            
            logger.info(f"Restored inputs for {len(selected_drugs)} drugs from session")
            return restored_inputs
            
        except Exception as e:
            logger.error(f"Error restoring inputs from session: {e}")
            return {}
    
    def get_session_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of session for display purposes.
        
        Args:
            session_data: Session data from database
            
        Returns:
            Dictionary with summary information
        """
        try:
            inputs_data = session_data.get('inputs', {})
            calculations = session_data.get('calculations', {})
            
            selected_drugs = inputs_data.get('selected_drugs', [])
            step = session_data.get('step', 0)
            completed_steps = session_data.get('completed_steps', [])
            
            # Calculate completion status
            is_complete = step >= 3 and 'final_results' in calculations
            has_calculations = bool(calculations.get('final_results'))
            
            summary = {
                'session_name': session_data.get('session_name', 'Unnamed Session'),
                'session_date': session_data.get('session_date', ''),
                'created_at': session_data.get('created_at', ''),
                'last_updated': session_data.get('last_updated', ''),
                'current_step': step,
                'completed_steps': completed_steps,
                'selected_drugs': selected_drugs,
                'drug_count': len(selected_drugs),
                'volume_unit': inputs_data.get('volume_unit', 'ml'),
                'weight_unit': inputs_data.get('weight_unit', 'mg'),
                'make_stock': inputs_data.get('make_stock', True),
                'is_complete': is_complete,
                'has_calculations': has_calculations,
                'status': 'Complete' if is_complete else f'Step {step}' if step > 0 else 'Not started'
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating session summary: {e}")
            return {}
    
    def validate_session_inputs(self, session_data: Dict[str, Any], 
                              required_step: int = 3) -> Tuple[bool, List[str]]:
        """Validate that session has required inputs for given step.
        
        Args:
            session_data: Session data to validate
            required_step: Minimum step required (1=drugs selected, 2=params entered, 3=weights entered)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            inputs_data = session_data.get('inputs', {})
            drug_inputs = inputs_data.get('drug_inputs', {})
            selected_drugs = inputs_data.get('selected_drugs', [])
            current_step = session_data.get('step', 0)
            
            # Check if session meets minimum step requirement
            if current_step < required_step:
                errors.append(f"Session is only at step {current_step}, but step {required_step} required")
            
            # Check for selected drugs
            if not selected_drugs:
                errors.append("No drugs selected in session")
            
            # Check drug inputs based on required step
            for i, drug_name in enumerate(selected_drugs):
                drug_data = drug_inputs.get(str(i), {})
                
                # Step 2 validation (parameters entered)
                if required_step >= 2:
                    if drug_data.get('mgit_tubes') is None:
                        errors.append(f"Missing MGIT tubes count for {drug_name}")
                    
                    # Additional validation for stock solutions
                    if inputs_data.get('make_stock', True):
                        if drug_data.get('stock_volume') is None:
                            errors.append(f"Missing stock volume for {drug_name}")
                        if drug_data.get('num_aliquots') is None:
                            errors.append(f"Missing aliquot count for {drug_name}")
                        if drug_data.get('ml_per_aliquot') is None:
                            errors.append(f"Missing aliquot volume for {drug_name}")
                
                # Step 3 validation (actual weights entered)  
                if required_step >= 3:
                    if drug_data.get('actual_weight') is None:
                        errors.append(f"Missing actual weight for {drug_name}")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info(f"Session validation passed for step {required_step}")
            else:
                logger.warning(f"Session validation failed: {errors}")
                
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error during session validation: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def create_new_session(self, user_id: int, session_name: str = None) -> Optional[int]:
        """Create a new session for the user.
        
        Args:
            user_id: User ID
            session_name: Optional session name, auto-generated if not provided
            
        Returns:
            Session ID if successful, None if failed
        """
        try:
            if not session_name:
                session_name = f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create initial session data
            initial_data = {
                'session_name': session_name,
                'step': 0,
                'completed_steps': [],
                'inputs': {},
                'calculations': {},
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            # Save to database
            session_id = self.db_manager.create_session(user_id, session_name, initial_data)
            
            if session_id:
                logger.info(f"Created new session {session_id} for user {user_id}")
            else:
                logger.error(f"Failed to create session for user {user_id}")
                
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating new session for user {user_id}: {e}")
            return None
    
    def delete_session(self, session_id: int, user_id: int) -> bool:
        """Delete a session (with user verification).
        
        Args:
            session_id: Session ID to delete
            user_id: User ID for security check
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            success = self.db_manager.delete_session(session_id, user_id)
            
            if success:
                logger.info(f"Deleted session {session_id} for user {user_id}")
            else:
                logger.warning(f"Failed to delete session {session_id} for user {user_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id} for user {user_id}: {e}")
            return False
    
    def list_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get list of all sessions for a user with summaries.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session summaries
        """
        try:
            sessions = self.db_manager.get_user_sessions(user_id)
            session_summaries = []
            
            for session in sessions:
                try:
                    session_data = json.loads(session[3]) if session[3] else {}
                    session_data['session_name'] = session[1]
                    session_data['session_date'] = session[2]
                    
                    summary = self.get_session_summary(session_data)
                    summary['session_id'] = session[0]
                    
                    session_summaries.append(summary)
                    
                except Exception as e:
                    logger.warning(f"Error processing session {session[0]}: {e}")
                    continue
            
            logger.info(f"Listed {len(session_summaries)} sessions for user {user_id}")
            return session_summaries
            
        except Exception as e:
            logger.error(f"Error listing sessions for user {user_id}: {e}")
            return []
