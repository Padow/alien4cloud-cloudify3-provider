from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.state import ctx_parameters as inputs
import subprocess
import os
import re
import sys
import time
import threading
from StringIO import StringIO
from cloudify_rest_client import CloudifyClient
from cloudify import utils

client = CloudifyClient(utils.get_manager_ip(), utils.get_manager_rest_service_port())


def get_host(entity):
    if entity.instance.relationships:
        for relationship in entity.instance.relationships:
            if 'cloudify.relationships.contained_in' in relationship.type_hierarchy:
                return relationship.target
    return None


def has_attribute_mapping(entity, attribute_name):
    ctx.logger.info('Check if it exists mapping for attribute {0} in {1}'.format(attribute_name, entity.node.properties))
    return ('_a4c_att_' + attribute_name) in entity.node.properties


def process_attribute_mapping(entity, attribute_name, data_retriever_function):
    # This is where attribute mapping is defined in the cloudify type
    mapping_configuration = entity.node.properties['_a4c_att_' + attribute_name]
    ctx.logger.info('Mapping configuration found for attribute {0} is {1}'.format(attribute_name, mapping_configuration))
    if mapping_configuration:
        # If the mapping configuration exist and if it concerns SELF then just get attribute of the mapped attribute name
        # Else if it concerns TARGET then follow the relationship and retrieved the mapped attribute name from the TARGET
        if mapping_configuration['parameters'][0] == 'SELF':
            return data_retriever_function(entity, mapping_configuration['parameters'][1])
        elif mapping_configuration['parameters'][0] == 'TARGET' and entity.instance.relationships:
            for relationship in entity.instance.relationships:
                if mapping_configuration['parameters'][1] in relationship.type_hierarchy:
                    return data_retriever_function(relationship.target, mapping_configuration['parameters'][2])
    return None


def get_attribute(entity, attribute_name):
    if has_attribute_mapping(entity, attribute_name):
        # First check if any mapping exist for attribute
        mapped_value = process_attribute_mapping(entity, attribute_name, get_attribute)
        ctx.logger.info('Mapping exists for attribute {0} with value {1}'.format(attribute_name, mapped_value))
        return mapped_value
    # No mapping exist, try to get directly the attribute from the entity
    attribute_value = entity.instance.runtime_properties.get(attribute_name, None)
    if attribute_value is not None:
        ctx.logger.info('Found the attribute {0} with value {1} on the node {2}'.format(attribute_name, attribute_value, entity.node.id))
        return attribute_value
    # Attribute retrieval fails, fall back to property
    property_value = entity.node.properties.get(attribute_name, None)
    if property_value is not None:
        return property_value
    # Property retrieval fails, fall back to host instance
    host = get_host(entity)
    if host is not None:
        ctx.logger.info('Attribute/Property not found {0} go up to the parent node {1}'.format(attribute_name, host.node.id))
        return get_attribute(host, attribute_name)
    # Nothing is found
    return ""


def _all_instances_get_attribute(entity, attribute_name):
    result_map = {}
    # get all instances data using cfy rest client
    # we have to get the node using the rest client with node_instance.node_id
    # then we will have the relationships
    node = client.nodes.get(ctx.deployment.id, entity.node.id)
    all_node_instances = client.node_instances.list(ctx.deployment.id, entity.node.id)
    for node_instance in all_node_instances:
        prop_value = __recursively_get_instance_data(node, node_instance, attribute_name)
        if prop_value is not None:
            ctx.logger.info('Found the property/attribute {0} with value {1} on the node {2} instance {3}'.format(attribute_name, prop_value, entity.node.id,
                                                                                                                  node_instance.id))
            result_map[node_instance.id + '_'] = prop_value
    return result_map


def get_property(entity, property_name):
    # Try to get the property value on the node
    property_value = entity.node.properties.get(property_name, None)
    if property_value is not None:
        ctx.logger.info('Found the property {0} with value {1} on the node {2}'.format(property_name, property_value, entity.node.id))
        return property_value
    # No property found on the node, fall back to the host
    host = get_host(entity)
    if host is not None:
        ctx.logger.info('Property not found {0} go up to the parent node {1}'.format(property_name, host.node.id))
        return get_property(host, property_name)
    return ""


def get_instance_list(node_id):
    result = ''
    all_node_instances = client.node_instances.list(ctx.deployment.id, node_id)
    for node_instance in all_node_instances:
        if len(result) > 0:
            result += ','
        result += node_instance.id
    return result


def __get_relationship(node, target_name, relationship_type):
    for relationship in node.relationships:
        if relationship.get('target_id') == target_name and relationship_type in relationship.get('type_hierarchy'):
            return relationship
    return None


def __has_attribute_mapping(node, attribute_name):
    ctx.logger.info('Check if it exists mapping for attribute {0} in {1}'.format(attribute_name, node.properties))
    return ('_a4c_att_' + attribute_name) in node.properties


def __process_attribute_mapping(node, node_instance, attribute_name, data_retriever_function):
    # This is where attribute mapping is defined in the cloudify type
    mapping_configuration = node.properties['_a4c_att_' + attribute_name]
    ctx.logger.info('Mapping configuration found for attribute {0} is {1}'.format(attribute_name, mapping_configuration))
    if mapping_configuration:
        # If the mapping configuration exist and if it concerns SELF then just get attribute of the mapped attribute name
        # Else if it concerns TARGET then follow the relationship and retrieved the mapped attribute name from the TARGET
        if mapping_configuration['parameters'][0] == 'SELF':
            return data_retriever_function(node, node_instance, mapping_configuration['parameters'][1])
        elif mapping_configuration['parameters'][0] == 'TARGET' and node_instance.relationships:
            for rel in node_instance.relationships:
                relationship = __get_relationship(node, rel.get('target_name'), rel.get('type'))
                if mapping_configuration['parameters'][1] in relationship.get('type_hierarchy'):
                    target_instance = client.node_instances.get(rel.get('target_id'))
                    target_node = client.nodes.get(ctx.deployment.id, target_instance.node_id)
                    return data_retriever_function(target_node, target_instance, mapping_configuration['parameters'][2])
    return None


def __recursively_get_instance_data(node, node_instance, attribute_name):
    if __has_attribute_mapping(node, attribute_name):
        return __process_attribute_mapping(node, node_instance, attribute_name, __recursively_get_instance_data)
    attribute_value = node_instance.runtime_properties.get(attribute_name, None)
    if attribute_value is not None:
        return attribute_value
    elif node_instance.relationships:
        for rel in node_instance.relationships:
            # on rel we have target_name, target_id (instanceId), type
            relationship = __get_relationship(node, rel.get('target_name'), rel.get('type'))
            if 'cloudify.relationships.contained_in' in relationship.get('type_hierarchy'):
                parent_instance = client.node_instances.get(rel.get('target_id'))
                parent_node = client.nodes.get(ctx.deployment.id, parent_instance.node_id)
                return __recursively_get_instance_data(parent_node, parent_instance, attribute_name)
        return None
    else:
        return None


def parse_output(output):
    # by convention, the last output is the result of the operation
    last_output = None
    outputs = {}
    pattern = re.compile('EXPECTED_OUTPUT_(\w+)=(.*)')
    for line in output.splitlines():
        match = pattern.match(line)
        if match is None:
            last_output = line
        else:
            output_name = match.group(1)
            output_value = match.group(2)
            outputs[output_name] = output_value
    return {'last_output': last_output, 'outputs': outputs}


def execute(script_path, process, outputNames):
    wrapper_path = ctx.download_resource("scriptWrapper.sh")
    os.chmod(wrapper_path, 0755)

    os.chmod(script_path, 0755)
    on_posix = 'posix' in sys.builtin_module_names

    env = os.environ.copy()
    process_env = process.get('env', {})
    env.update(process_env)

    if outputNames is not None:
        env['EXPECTED_OUTPUTS'] = outputNames
        command = '{0} {1}'.format(wrapper_path, script_path)
    else:
        command = script_path

    ctx.logger.info('Executing: {0} in env {1}'.format(command, env))

    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env=env,
                               cwd=None,
                               bufsize=1,
                               close_fds=on_posix)

    return_code = None

    stdout_consumer = OutputConsumer(process.stdout)
    stderr_consumer = OutputConsumer(process.stderr)

    while True:
        return_code = process.poll()
        if return_code is not None:
            break
        time.sleep(0.1)

    stdout_consumer.join()
    stderr_consumer.join()

    parsed_output = parse_output(stdout_consumer.buffer.getvalue())
    if outputNames is not None:
        outputNameList = outputNames.split(';')
        for outputName in outputNameList:
            ctx.logger.info('Ouput name: {0} value : {1}'.format(outputName, parsed_output['outputs'][outputName]))

    ok_message = "Script {0} executed normally with standard output {1} and error output {2}".format(command, stdout_consumer.buffer.getvalue(),
                                                                                                     stderr_consumer.buffer.getvalue())
    error_message = "Script {0} encountered error with return code {1} and standard output {2}, error output {3}".format(command, return_code,
                                                                                                                         stdout_consumer.buffer.getvalue(),
                                                                                                                         stderr_consumer.buffer.getvalue())
    if return_code != 0:
        ctx.logger.error(error_message)
        raise NonRecoverableError(error_message)
    else:
        ctx.logger.info(ok_message)

    return parsed_output


class OutputConsumer(object):
    def __init__(self, out):
        self.out = out
        self.buffer = StringIO()
        self.consumer = threading.Thread(target=self.consume_output)
        self.consumer.daemon = True
        self.consumer.start()

    def consume_output(self):
        for line in iter(self.out.readline, b''):
            self.buffer.write(line)
        self.out.close()

    def join(self):
        self.consumer.join()
