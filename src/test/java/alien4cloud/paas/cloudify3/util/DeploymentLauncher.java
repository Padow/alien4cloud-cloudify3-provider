package alien4cloud.paas.cloudify3.util;

import java.util.Map;

import javax.annotation.Resource;

import org.springframework.stereotype.Component;

import alien4cloud.common.AlienConstants;
import alien4cloud.it.Context;
import alien4cloud.model.deployment.DeploymentTopology;
import alien4cloud.model.orchestrators.locations.Location;
import alien4cloud.model.topology.Topology;
import alien4cloud.paas.IPaaSCallback;
import alien4cloud.paas.cloudify3.CloudifyOrchestrator;
import alien4cloud.paas.cloudify3.configuration.CloudConfiguration;
import alien4cloud.paas.cloudify3.configuration.CloudConfigurationHolder;
import alien4cloud.paas.cloudify3.restclient.BlueprintClient;
import alien4cloud.paas.exception.PluginConfigurationException;
import alien4cloud.paas.model.PaaSTopologyDeploymentContext;
import alien4cloud.paas.plan.TopologyTreeBuilderService;
import alien4cloud.paas.wf.WorkflowsBuilderService;
import alien4cloud.paas.wf.WorkflowsBuilderService.TopologyContext;
import alien4cloud.utils.ReflectionUtil;

import com.google.common.collect.Maps;
import com.google.common.util.concurrent.SettableFuture;

@Component
public class DeploymentLauncher {

    @Resource
    private ApplicationUtil applicationUtil;

    @Resource
    private TopologyTreeBuilderService topologyTreeBuilderService;

    @Resource
    private CloudifyOrchestrator cloudifyPaaSProvider;

    @Resource
    private WorkflowsBuilderService workflowBuilderService;

    @Resource
    private CloudConfigurationHolder cloudConfigurationHolder;

    @Resource
    private BlueprintClient blueprintDAO;

    private boolean initialized = false;

    public synchronized void initializeCloudifyManagerConnection() throws PluginConfigurationException {
        // Lazily initialize cloudify connection as test does not need this
        // It's for people who use TestDeploymentService to perform manual testing
        if (initialized) {
            return;
        }
        CloudConfiguration cloudConfiguration = cloudConfigurationHolder.getConfiguration();
        String cloudifyURL = System.getenv("CLOUDIFY_URL");
        if (cloudifyURL == null) {
            cloudifyURL = Context.getInstance().getCloudify3ManagerUrl();
        }
        cloudConfiguration.setUrl(cloudifyURL);
        cloudConfigurationHolder.setConfigurationAndNotifyListeners(cloudConfiguration);
        initialized = true;
    }

    public PaaSTopologyDeploymentContext buildPaaSDeploymentContext(String appName, String topologyName, String locationName) {
        Topology topology = applicationUtil.createAlienApplication(appName, topologyName, locationName);
        // init the workflows
        TopologyContext topologyContext = workflowBuilderService.buildTopologyContext(topology);
        workflowBuilderService.initWorkflows(topologyContext);
        DeploymentTopology deploymentTopology = new DeploymentTopology();
        ReflectionUtil.mergeObject(topology, deploymentTopology, "id");
        PaaSTopologyDeploymentContext deploymentContext = new PaaSTopologyDeploymentContext();
        deploymentContext.setPaaSTopology(topologyTreeBuilderService.buildPaaSTopology(topology));
        deploymentContext.setDeploymentTopology(deploymentTopology);
        alien4cloud.model.deployment.Deployment deployment = new alien4cloud.model.deployment.Deployment();
        deployment.setId(appName);
        deployment.setOrchestratorDeploymentId(appName);
        deploymentContext.setDeployment(deployment);
        Map<String, Location> locationMap = Maps.newHashMap();
        Location location = new Location();
        location.setInfrastructureType(locationName);
        locationMap.put(AlienConstants.GROUP_ALL, location);
        deploymentContext.setLocations(locationMap);
        return deploymentContext;
    }

    public void launch(PaaSTopologyDeploymentContext deploymentContext) throws Exception {
        initializeCloudifyManagerConnection();
        final SettableFuture<Object> future = SettableFuture.create();
        cloudifyPaaSProvider.deploy(deploymentContext, new IPaaSCallback<Object>() {

            @Override
            public void onSuccess(Object data) {
                future.set(data);
            }

            @Override
            public void onFailure(Throwable throwable) {
                future.setException(throwable);
            }
        });
        future.get();
    }

    public String launch(String topologyName, String locationName) throws Exception {
        StackTraceElement[] stackTraceElements = Thread.currentThread().getStackTrace();
        String deploymentId = stackTraceElements[2].getMethodName();
        launch(buildPaaSDeploymentContext(deploymentId, topologyName, locationName));
        return deploymentId;
    }

    public String launch(String topologyName) throws Exception {
        return launch(topologyName, "openstack");
    }

    public void verifyBlueprintUpload(String topology, String path) throws PluginConfigurationException {
        initializeCloudifyManagerConnection();
        // Check if cloudify accept the blueprint
        blueprintDAO.create(topology, path);
        blueprintDAO.delete(topology);
    }
}