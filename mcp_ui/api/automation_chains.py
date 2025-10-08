"""
Automation Chains API
Simple workflow alternative when NextAI is not installed
Allows chaining MCP tools together in sequence
"""
import frappe
import json
from typing import List, Dict, Any


@frappe.whitelist()
def get_chains():
	"""
	Get all automation chains for current user
	
	Returns:
		List of automation chains
	"""
	chains = frappe.get_all(
		"MCP Automation Chain",
		filters={"owner": frappe.session.user},
		fields=["name", "chain_name", "description", "steps", "enabled", "modified"],
		order_by="modified desc"
	)
	
	return {
		"success": True,
		"chains": chains,
		"count": len(chains)
	}


@frappe.whitelist()
def create_chain(chain_name, description, steps):
	"""
	Create a new automation chain
	
	Args:
		chain_name: Name of the chain
		description: Description
		steps: JSON string of steps [{tool, params, next_step_condition}, ...]
	"""
	try:
		steps_list = json.loads(steps) if isinstance(steps, str) else steps
		
		chain = frappe.get_doc({
			"doctype": "MCP Automation Chain",
			"chain_name": chain_name,
			"description": description,
			"steps": json.dumps(steps_list),
			"enabled": 1
		})
		chain.insert()
		
		return {
			"success": True,
			"chain_name": chain.name,
			"message": f"Chain '{chain_name}' created successfully"
		}
	except Exception as e:
		frappe.log_error(f"Chain creation error: {str(e)}")
		return {
			"success": False,
			"message": str(e)
		}


@frappe.whitelist()
def execute_chain(chain_name, initial_data=None):
	"""
	Execute an automation chain
	
	Args:
		chain_name: Name of the chain to execute
		initial_data: JSON string of initial data/variables
		
	Returns:
		Execution results
	"""
	try:
		chain = frappe.get_doc("MCP Automation Chain", chain_name)
		
		if not chain.enabled:
			frappe.throw("Chain is disabled")
		
		steps = json.loads(chain.steps)
		initial = json.loads(initial_data) if initial_data else {}
		
		# Execute chain
		results = _execute_chain_steps(steps, initial)
		
		# Log execution
		log = frappe.get_doc({
			"doctype": "MCP Chain Execution Log",
			"chain": chain_name,
			"status": "Completed" if results["success"] else "Failed",
			"input_data": initial_data or "{}",
			"output_data": json.dumps(results),
			"steps_executed": results.get("steps_completed", 0)
		})
		log.insert()
		
		return results
		
	except Exception as e:
		frappe.log_error(f"Chain execution error: {str(e)}")
		return {
			"success": False,
			"message": str(e),
			"steps_completed": 0,
			"results": []
		}


def _execute_chain_steps(steps: List[Dict], variables: Dict) -> Dict[str, Any]:
	"""
	Execute chain steps in sequence
	
	Args:
		steps: List of step definitions
		variables: Initial variables
		
	Returns:
		Execution results
	"""
	from mcp_ui.api.tools import execute_tool
	
	results = []
	current_vars = {**variables}
	
	for idx, step in enumerate(steps):
		try:
			tool_name = step.get("tool")
			params = step.get("params", {})
			
			# Replace variables in params
			resolved_params = _resolve_variables(params, current_vars)
			
			# Execute tool
			result = execute_tool(tool_name, json.dumps(resolved_params))
			
			# Store result in variables
			output_var = step.get("output_variable", f"step_{idx}_result")
			current_vars[output_var] = result.get("result")
			
			results.append({
				"step": idx + 1,
				"tool": tool_name,
				"status": "success",
				"result": result.get("result")
			})
			
			# Check if we should continue
			condition = step.get("next_step_condition")
			if condition and not _evaluate_condition(condition, current_vars):
				break
				
		except Exception as e:
			results.append({
				"step": idx + 1,
				"tool": step.get("tool"),
				"status": "failed",
				"error": str(e)
			})
			
			# Stop on error unless continue_on_error is set
			if not step.get("continue_on_error"):
				return {
					"success": False,
					"message": f"Failed at step {idx + 1}: {str(e)}",
					"steps_completed": idx,
					"results": results,
					"variables": current_vars
				}
	
	return {
		"success": True,
		"message": "Chain executed successfully",
		"steps_completed": len(results),
		"results": results,
		"variables": current_vars
	}


def _resolve_variables(params: Dict, variables: Dict) -> Dict:
	"""
	Replace variable placeholders in params with actual values
	
	Args:
		params: Parameters dict
		variables: Available variables
		
	Returns:
		Resolved parameters
	"""
	resolved = {}
	
	for key, value in params.items():
		if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
			var_name = value[2:-1]
			resolved[key] = variables.get(var_name, value)
		elif isinstance(value, dict):
			resolved[key] = _resolve_variables(value, variables)
		else:
			resolved[key] = value
	
	return resolved


def _evaluate_condition(condition: str, variables: Dict) -> bool:
	"""
	Evaluate a condition string
	
	Args:
		condition: Condition string (e.g., "${result.success} == true")
		variables: Available variables
		
	Returns:
		Boolean result
	"""
	try:
		# Simple condition evaluation
		# Replace variables
		for var_name, var_value in variables.items():
			condition = condition.replace(f"${{{var_name}}}", str(var_value))
		
		# Evaluate (simplified - in production use a safer evaluator)
		return eval(condition)
	except:
		return True  # Continue by default if condition can't be evaluated


@frappe.whitelist()
def delete_chain(chain_name):
	"""Delete an automation chain"""
	try:
		frappe.delete_doc("MCP Automation Chain", chain_name)
		return {
			"success": True,
			"message": f"Chain '{chain_name}' deleted"
		}
	except Exception as e:
		return {
			"success": False,
			"message": str(e)
		}


@frappe.whitelist()
def toggle_chain(chain_name, enabled):
	"""Enable or disable a chain"""
	try:
		chain = frappe.get_doc("MCP Automation Chain", chain_name)
		chain.enabled = int(enabled)
		chain.save()
		
		return {
			"success": True,
			"message": f"Chain {'enabled' if enabled else 'disabled'}"
		}
	except Exception as e:
		return {
			"success": False,
			"message": str(e)
		}

