from cloudify.decorators import workflow
from cloudify.workflows import ctx
from cloudify.workflows import tasks as workflow_tasks
from utils import set_state_task
from utils import operation_task
from utils import link_tasks
from utils import CustomContext
from utils import generate_native_node_workflows
from utils import _get_all_nodes
from utils import _get_all_nodes_instances
from utils import _get_all_modified_nodes
from utils import is_host_node
from workflow import WfStartEvent
from workflow import build_pre_event


# subworkflow 'install' for host 'Compute'
def install_host_compute(ctx, graph, custom_context):
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'starting', 'FileSystem_starting', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'configuring', 'FileSystem_configuring', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'configured', 'FileSystem_configured', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'initial', 'FileSystem_initial', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'created', 'FileSystem_created', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'creating', 'FileSystem_creating', custom_context)
    operation_task(ctx, graph, 'FileSystem', 'cloudify.interfaces.lifecycle.configure', 'configure_FileSystem', custom_context)
    custom_context.register_native_delegate_wf_step('Compute', 'Compute_install')
    operation_task(ctx, graph, 'FileSystem', 'cloudify.interfaces.lifecycle.start', 'start_FileSystem', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'started', 'FileSystem_started', custom_context)
    generate_native_node_workflows(ctx, graph, custom_context, 'install')
    link_tasks(graph, 'start_FileSystem', 'FileSystem_starting', custom_context)
    link_tasks(graph, 'configure_FileSystem', 'FileSystem_configuring', custom_context)
    link_tasks(graph, 'FileSystem_starting', 'FileSystem_configured', custom_context)
    link_tasks(graph, 'FileSystem_creating', 'FileSystem_initial', custom_context)
    link_tasks(graph, 'FileSystem_configuring', 'FileSystem_created', custom_context)
    link_tasks(graph, 'FileSystem_created', 'FileSystem_creating', custom_context)
    link_tasks(graph, 'FileSystem_configured', 'configure_FileSystem', custom_context)
    link_tasks(graph, 'FileSystem_initial', 'Compute_install', custom_context)
    link_tasks(graph, 'FileSystem_started', 'start_FileSystem', custom_context)


# subworkflow 'uninstall' for host 'Compute'
def uninstall_host_compute(ctx, graph, custom_context):
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'deleting', 'FileSystem_deleting', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'deleted', 'FileSystem_deleted', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'stopping', 'FileSystem_stopping', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'stopped', 'FileSystem_stopped', custom_context)
    operation_task(ctx, graph, 'FileSystem', 'cloudify.interfaces.lifecycle.stop', 'stop_FileSystem', custom_context)
    custom_context.register_native_delegate_wf_step('Compute', 'Compute_uninstall')
    generate_native_node_workflows(ctx, graph, custom_context, 'uninstall')
    link_tasks(graph, 'FileSystem_deleted', 'FileSystem_deleting', custom_context)
    link_tasks(graph, 'Compute_uninstall', 'FileSystem_deleted', custom_context)
    link_tasks(graph, 'stop_FileSystem', 'FileSystem_stopping', custom_context)
    link_tasks(graph, 'FileSystem_deleting', 'FileSystem_stopped', custom_context)
    link_tasks(graph, 'FileSystem_stopped', 'stop_FileSystem', custom_context)


def install_host(ctx, graph, custom_context, compute):
    options = {}
    options['Compute'] = install_host_compute
    options[compute](ctx, graph, custom_context)


def uninstall_host(ctx, graph, custom_context, compute):
    options = {}
    options['Compute'] = uninstall_host_compute
    options[compute](ctx, graph, custom_context)


@workflow
def a4c_install(**kwargs):
    graph = ctx.graph_mode()
    nodes = _get_all_nodes(ctx)
    custom_context = CustomContext(ctx, nodes, nodes)
    ctx.internal.send_workflow_event(event_type='a4c_workflow_started', message=build_pre_event(WfStartEvent('install')))
    _a4c_install(ctx, graph, custom_context)
    return graph.execute()


@workflow
def a4c_uninstall(**kwargs):
    graph = ctx.graph_mode()
    nodes = _get_all_nodes(ctx)
    custom_context = CustomContext(ctx, nodes, nodes)
    ctx.internal.send_workflow_event(event_type='a4c_workflow_started', message=build_pre_event(WfStartEvent('uninstall')))
    _a4c_uninstall(ctx, graph, custom_context)
    return graph.execute()


def _a4c_install(ctx, graph, custom_context):
    #  following code can be pasted in src/test/python/workflows/tasks.py for simulation
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'starting', 'FileSystem_starting', custom_context)
    custom_context.register_native_delegate_wf_step('BlockStorage', 'BlockStorage_install')
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'configured', 'FileSystem_configured', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'configuring', 'FileSystem_configuring', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'initial', 'FileSystem_initial', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'created', 'FileSystem_created', custom_context)
    operation_task(ctx, graph, 'FileSystem', 'cloudify.interfaces.lifecycle.configure', 'configure_FileSystem', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'creating', 'FileSystem_creating', custom_context)
    operation_task(ctx, graph, 'FileSystem', 'cloudify.interfaces.lifecycle.start', 'start_FileSystem', custom_context)
    custom_context.register_native_delegate_wf_step('Compute', 'Compute_install')
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'started', 'FileSystem_started', custom_context)
    custom_context.register_native_delegate_wf_step('DeletableBlockStorage', 'DeletableBlockStorage_install')
    generate_native_node_workflows(ctx, graph, custom_context, 'install')
    link_tasks(graph, 'FileSystem_starting', 'FileSystem_configured', custom_context)
    link_tasks(graph, 'FileSystem_configured', 'configure_FileSystem', custom_context)
    link_tasks(graph, 'FileSystem_configuring', 'FileSystem_created', custom_context)
    link_tasks(graph, 'FileSystem_initial', 'BlockStorage_install', custom_context)
    link_tasks(graph, 'FileSystem_initial', 'Compute_install', custom_context)
    link_tasks(graph, 'FileSystem_created', 'FileSystem_creating', custom_context)
    link_tasks(graph, 'configure_FileSystem', 'FileSystem_configuring', custom_context)
    link_tasks(graph, 'FileSystem_creating', 'FileSystem_initial', custom_context)
    link_tasks(graph, 'start_FileSystem', 'FileSystem_starting', custom_context)
    link_tasks(graph, 'FileSystem_started', 'start_FileSystem', custom_context)


@workflow
def a4c_scale(ctx, node_id, delta, scale_compute, **kwargs):

    scaled_node = ctx.get_node(node_id)
    if not scaled_node:
        raise ValueError("Node {0} doesn't exist".format(node_id))
    if not is_host_node(scaled_node):
        raise ValueError("Node {0} is not a host. This workflow can only scale hosts".format(node_id))
    if delta == 0:
        ctx.logger.info('delta parameter is 0, so no scaling will take place.')
        return

    curr_num_instances = scaled_node.number_of_instances
    planned_num_instances = curr_num_instances + delta
    if planned_num_instances < 1:
        raise ValueError('Provided delta: {0} is illegal. current number of'
                         'instances of node {1} is {2}'
                         .format(delta, node_id, curr_num_instances))

    modification = ctx.deployment.start_modification({
        scaled_node.id: {
            'instances': planned_num_instances
        }
    })
    ctx.logger.info('Deployment modification started. [modification_id={0} : {1}]'.format(modification.id, dir(modification)))
    #ctx.logger.info('Deployment modification started. [modification.added={0} : {1}]'.format(modification.id, dir(modification.added)))
    try:
        if delta > 0:
            ctx.logger.info('Scaling host {0} adding {1} instances'.format(node_id, delta))
            added_and_related = _get_all_nodes(modification.added)
            added = _get_all_modified_nodes(added_and_related, 'added')
            graph = ctx.graph_mode()
            ctx.internal.send_workflow_event(event_type='a4c_workflow_started', message=build_pre_event(WfStartEvent('scale', 'install')))
            custom_context = CustomContext(ctx, added, added_and_related)
            install_host(ctx, graph, custom_context, node_id)
            try:
                graph.execute()
            except:
                ctx.logger.error('Scale failed.')
        else:
            ctx.logger.info('Unscaling host {0} removing {1} instances'.format(node_id, delta))
            removed_and_related = _get_all_nodes(modification.removed)
            removed = _get_all_modified_nodes(removed_and_related, 'removed')
            graph = ctx.graph_mode()
            ctx.internal.send_workflow_event(event_type='a4c_workflow_started', message=build_pre_event(WfStartEvent('scale', 'uninstall')))
            custom_context = CustomContext(ctx, removed, removed_and_related)
            uninstall_host(ctx, graph, custom_context, node_id)
            try:
                graph.execute()
            except:
                ctx.logger.error('Unscale failed.')
    except:
        ctx.logger.warn('Rolling back deployment modification. [modification_id={0}]'.format(modification.id))
        try:
            modification.rollback()
        except:
            ctx.logger.warn('Deployment modification rollback failed. The '
                            'deployment model is most likely in some corrupted'
                            ' state.'
                            '[modification_id={0}]'.format(modification.id))
            raise
        raise
    else:
        try:
            modification.finish()
        except:
            ctx.logger.warn('Deployment modification finish failed. The '
                            'deployment model is most likely in some corrupted'
                            ' state.'
                            '[modification_id={0}]'.format(modification.id))
            raise

def _a4c_uninstall(ctx, graph, custom_context):
    #  following code can be pasted in src/test/python/workflows/tasks.py for simulation
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'deleting', 'FileSystem_deleting', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'deleted', 'FileSystem_deleted', custom_context)
    custom_context.register_native_delegate_wf_step('BlockStorage', 'BlockStorage_uninstall')
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'stopped', 'FileSystem_stopped', custom_context)
    custom_context.add_customized_wf_node('FileSystem')
    set_state_task(ctx, graph, 'FileSystem', 'stopping', 'FileSystem_stopping', custom_context)
    operation_task(ctx, graph, 'FileSystem', 'cloudify.interfaces.lifecycle.stop', 'stop_FileSystem', custom_context)
    custom_context.register_native_delegate_wf_step('DeletableBlockStorage', 'DeletableBlockStorage_uninstall')
    custom_context.register_native_delegate_wf_step('Compute', 'Compute_uninstall')
    generate_native_node_workflows(ctx, graph, custom_context, 'uninstall')
    link_tasks(graph, 'FileSystem_deleting', 'FileSystem_stopped', custom_context)
    link_tasks(graph, 'FileSystem_deleted', 'FileSystem_deleting', custom_context)
    link_tasks(graph, 'BlockStorage_uninstall', 'FileSystem_deleted', custom_context)
    link_tasks(graph, 'FileSystem_stopped', 'stop_FileSystem', custom_context)
    link_tasks(graph, 'stop_FileSystem', 'FileSystem_stopping', custom_context)
    link_tasks(graph, 'Compute_uninstall', 'FileSystem_deleted', custom_context)


@workflow
def a4c_scale(ctx, node_id, delta, scale_compute, **kwargs):

    scaled_node = ctx.get_node(node_id)
    if not scaled_node:
        raise ValueError("Node {0} doesn't exist".format(node_id))
    if not is_host_node(scaled_node):
        raise ValueError("Node {0} is not a host. This workflow can only scale hosts".format(node_id))
    if delta == 0:
        ctx.logger.info('delta parameter is 0, so no scaling will take place.')
        return

    curr_num_instances = scaled_node.number_of_instances
    planned_num_instances = curr_num_instances + delta
    if planned_num_instances < 1:
        raise ValueError('Provided delta: {0} is illegal. current number of'
                         'instances of node {1} is {2}'
                         .format(delta, node_id, curr_num_instances))

    modification = ctx.deployment.start_modification({
        scaled_node.id: {
            'instances': planned_num_instances
        }
    })
    ctx.logger.info('Deployment modification started. [modification_id={0} : {1}]'.format(modification.id, dir(modification)))
    #ctx.logger.info('Deployment modification started. [modification.added={0} : {1}]'.format(modification.id, dir(modification.added)))
    try:
        if delta > 0:
            ctx.logger.info('Scaling host {0} adding {1} instances'.format(node_id, delta))
            added_and_related = _get_all_nodes(modification.added)
            added = _get_all_modified_nodes(added_and_related, 'added')
            graph = ctx.graph_mode()
            ctx.internal.send_workflow_event(event_type='a4c_workflow_started', message=build_pre_event(WfStartEvent('scale', 'install')))
            custom_context = CustomContext(ctx, added, added_and_related)
            install_host(ctx, graph, custom_context, node_id)
            try:
                graph.execute()
            except:
                ctx.logger.error('Scale failed.')
        else:
            ctx.logger.info('Unscaling host {0} removing {1} instances'.format(node_id, delta))
            removed_and_related = _get_all_nodes(modification.removed)
            removed = _get_all_modified_nodes(removed_and_related, 'removed')
            graph = ctx.graph_mode()
            ctx.internal.send_workflow_event(event_type='a4c_workflow_started', message=build_pre_event(WfStartEvent('scale', 'uninstall')))
            custom_context = CustomContext(ctx, removed, removed_and_related)
            uninstall_host(ctx, graph, custom_context, node_id)
            try:
                graph.execute()
            except:
                ctx.logger.error('Unscale failed.')
    except:
        ctx.logger.warn('Rolling back deployment modification. [modification_id={0}]'.format(modification.id))
        try:
            modification.rollback()
        except:
            ctx.logger.warn('Deployment modification rollback failed. The '
                            'deployment model is most likely in some corrupted'
                            ' state.'
                            '[modification_id={0}]'.format(modification.id))
            raise
        raise
    else:
        try:
            modification.finish()
        except:
            ctx.logger.warn('Deployment modification finish failed. The '
                            'deployment model is most likely in some corrupted'
                            ' state.'
                            '[modification_id={0}]'.format(modification.id))
            raise

#following code can be pasted in src/test/python/workflows/context.py for simulation
#def _build_nodes(ctx):
    #types = []
    #types.append('alien.nodes.LinuxFileSystem')
    #types.append('tosca.nodes.SoftwareComponent')
    #types.append('tosca.nodes.Root')
    #node_FileSystem = _build_node(ctx, 'FileSystem', types, 1)
    #types = []
    #types.append('alien.nodes.openstack.ScalableCompute')
    #types.append('alien.nodes.openstack.Compute')
    #types.append('tosca.nodes.Compute')
    #types.append('tosca.nodes.Root')
    #node_Compute = _build_node(ctx, 'Compute', types, 1)
    #_add_relationship(node_FileSystem, node_Compute)
