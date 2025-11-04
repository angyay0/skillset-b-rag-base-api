from flask import request, jsonify
from src.application.services.report_request_service import ReportRequestService


class ReportRequestController:
    """Controller for report request endpoints"""
    
    def __init__(self, report_request_service: ReportRequestService):
        self.report_request_service = report_request_service
    
    def create_report_request(self):
        """Create a new report request"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400
            
            # Validar que los campos requeridos existan
            required_fields = ['agent_id', 'metrics', 'format', 'requested_by']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400
            
            # Crear la solicitud de reporte
            report_request = self.report_request_service.create_report_request(data)
            
            # Responder con 201 y los datos de la solicitud creada
            response_data = self.report_request_service._to_response_dict(report_request)
            
            return jsonify({
                'message': 'Report request created successfully',
                'data': response_data
            }), 201
            
        except ValueError as e:
            return jsonify({
                'error': 'Validation error',
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500
    
    def get_report_request(self, request_id):
        """Get a report request by ID"""
        try:
            request_data = self.report_request_service.get_request_by_id(request_id)

            if not request_data:
                return jsonify({
                    'error': 'Not found',
                    'message': f'Report request with ID {request_id} not found'
                }), 404

            return jsonify({
                'message': 'Report request retrieved successfully',
                'data': request_data
            }), 200

        except ValueError as e:
            return jsonify({
                'error': 'Bad request',
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def get_all_report_requests(self):
        """Get all report requests"""
        try:
            # Need to add this method to the service
            requests_data = self.report_request_service.get_all_requests()

            return jsonify({
                'message': 'Report requests retrieved successfully',
                'data': requests_data,
                'count': len(requests_data)
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500
