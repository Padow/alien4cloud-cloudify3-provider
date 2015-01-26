package alien4cloud.paas.cloudify3;

import java.io.IOException;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import javax.annotation.Resource;

import org.junit.Before;
import org.junit.BeforeClass;

import alien4cloud.model.application.DeploymentSetup;
import alien4cloud.model.cloud.CloudResourceMatcherConfig;
import alien4cloud.model.cloud.ComputeTemplate;
import alien4cloud.model.cloud.MatchedComputeTemplate;
import alien4cloud.model.cloud.MatchedNetwork;
import alien4cloud.model.cloud.Network;
import alien4cloud.model.topology.NodeTemplate;
import alien4cloud.model.topology.Topology;
import alien4cloud.paas.cloudify3.configuration.CloudConfiguration;
import alien4cloud.paas.cloudify3.configuration.CloudConfigurationHolder;
import alien4cloud.paas.cloudify3.configuration.Flavor;
import alien4cloud.paas.cloudify3.configuration.Image;
import alien4cloud.paas.cloudify3.configuration.Subnet;
import alien4cloud.paas.cloudify3.service.ComputeTemplateMatcherService;
import alien4cloud.paas.cloudify3.service.NetworkMatcherService;
import alien4cloud.paas.cloudify3.util.CSARUtil;
import alien4cloud.tosca.normative.NormativeComputeConstants;
import alien4cloud.tosca.normative.NormativeNetworkConstants;
import alien4cloud.utils.FileUtil;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

public class AbstractTest {

    public static final String SINGLE_COMPUTE_TOPOLOGY = "single_compute";

    public static final String SINGLE_COMPUTE_TOPOLOGY_WITH_APACHE = "single_compute_with_apache";

    public static final String SINGLE_COMPUTE_TOPOLOGY_WITH_MYSQL = "single_compute_with_mysql";

    public static final String LAMP_TOPOLOGY = "lamp";

    public static final String NETWORK_TOPOLOGY = "network";

    private ComputeTemplate computeTemplate = new ComputeTemplate("alien_image", "alien_flavor");

    private Network network = new Network(4, "", "net-pub", "");

    private Network internalNetwork = new Network(4, "", "internal-network", "");

    @Resource
    private CloudConfigurationHolder cloudConfigurationHolder;

    @Resource
    private ComputeTemplateMatcherService computeTemplateMatcherService;

    @Resource
    private NetworkMatcherService networkMatcherService;

    @Resource
    private CSARUtil csarUtil;

    @BeforeClass
    public static void cleanup() throws IOException {
        FileUtil.delete(CSARUtil.ARTIFACTS_DIRECTORY);
        FileUtil.delete(Paths.get("target/alien"));
    }

    @Before
    public void before() throws Exception {
        CloudConfiguration cloudConfiguration = new CloudConfiguration();
        cloudConfiguration.setUrl("http://129.185.67.107:8100");
        cloudConfiguration.setImages(Sets.newHashSet(new Image("727df994-2e1b-404e-9276-b248223a835d", "Ubuntu Precise")));
        cloudConfiguration.setFlavors(Sets.newHashSet(new Flavor("3", "Medium")));
        cloudConfiguration.setNetworks(Sets.newHashSet(
                new alien4cloud.paas.cloudify3.configuration.Network("net-pub", "Public Network", true, null),
                new alien4cloud.paas.cloudify3.configuration.Network("internal-network", "Internal Network", false, Sets.newHashSet(new Subnet(
                        "internal-network-subnet", "Internal Network Subnet", 4, "192.168.1.0/24")))));
        cloudConfigurationHolder.setConfiguration(cloudConfiguration);
        CloudResourceMatcherConfig matcherConfig = new CloudResourceMatcherConfig();
        matcherConfig.setMatchedComputeTemplates(Lists.newArrayList(new MatchedComputeTemplate(computeTemplate, "Medium_Ubuntu_Precise")));
        matcherConfig.setMatchedNetworks(Lists.newArrayList(new MatchedNetwork(network, "net-pub"), new MatchedNetwork(internalNetwork, "internal-network")));
        computeTemplateMatcherService.configure(matcherConfig.getComputeTemplateMapping());
        networkMatcherService.configure(matcherConfig.getNetworkMapping());
        csarUtil.uploadAll();
    }

    protected DeploymentSetup generateDeploymentSetup(Topology topology) {
        List<String> nodeIds = Lists.newArrayList();
        List<String> networkIds = Lists.newArrayList();
        for (Map.Entry<String, NodeTemplate> nodeTemplateEntry : topology.getNodeTemplates().entrySet()) {
            if (NormativeComputeConstants.COMPUTE_TYPE.equals(nodeTemplateEntry.getValue().getType())) {
                nodeIds.add(nodeTemplateEntry.getKey());
            }
            if (NormativeNetworkConstants.NETWORK_TYPE.equals(nodeTemplateEntry.getValue().getType())) {
                networkIds.add(nodeTemplateEntry.getKey());
            }
        }
        DeploymentSetup deploymentSetup = new DeploymentSetup();

        Map<String, ComputeTemplate> resourcesMapping = Maps.newHashMap();
        deploymentSetup.setCloudResourcesMapping(resourcesMapping);
        for (String nodeId : nodeIds) {
            resourcesMapping.put(nodeId, computeTemplate);
        }

        Map<String, Network> networkMapping = Maps.newHashMap();
        deploymentSetup.setNetworkMapping(networkMapping);
        for (String networkId : networkIds) {
            switch (networkId) {
            case "NetPub":
                networkMapping.put(networkId, network);
                break;
            case "internal-network":
                networkMapping.put(networkId, internalNetwork);
                break;
            default:
                throw new RuntimeException("Not configured " + networkId);
            }

        }

        return deploymentSetup;
    }
}
