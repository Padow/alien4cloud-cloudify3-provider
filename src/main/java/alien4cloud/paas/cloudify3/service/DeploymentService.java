package alien4cloud.paas.cloudify3.service;

import java.io.IOException;
import java.nio.file.Path;
import java.util.concurrent.Callable;
import java.util.concurrent.TimeUnit;

import javax.annotation.Resource;

import lombok.extern.slf4j.Slf4j;

import org.springframework.stereotype.Component;

import alien4cloud.component.repository.exception.CSARVersionNotFoundException;
import alien4cloud.paas.cloudify3.dao.BlueprintDAO;
import alien4cloud.paas.cloudify3.model.Blueprint;
import alien4cloud.paas.cloudify3.model.Deployment;
import alien4cloud.paas.cloudify3.model.Execution;
import alien4cloud.paas.cloudify3.model.Workflow;
import alien4cloud.paas.cloudify3.service.model.CloudifyDeployment;
import alien4cloud.paas.model.DeploymentStatus;
import alien4cloud.paas.model.PaaSDeploymentContext;
import alien4cloud.utils.FileUtil;

import com.google.common.collect.Maps;
import com.google.common.util.concurrent.AsyncFunction;
import com.google.common.util.concurrent.FutureCallback;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;

/**
 * Handle deployment of the topology on cloudify 3. This service handle from the creation of blueprint from alien model to execution of default workflow
 * install, uninstall.
 *
 * @author Minh Khang VU
 */
@Component("cloudify-deployment-service")
@Slf4j
public class DeploymentService extends RuntimeService {

    @Resource
    private BlueprintService blueprintService;

    @Resource
    private BlueprintDAO blueprintDAO;

    @Resource
    private EventService eventService;

    public ListenableFuture<Execution> deploy(final CloudifyDeployment alienDeployment) {
        // Cloudify 3 will use recipe id to identify a blueprint and a deployment instead of deployment id
        log.info("Deploying {} for alien deployment {}", alienDeployment.getDeploymentPaaSId(), alienDeployment.getDeploymentId());
        eventService.registerDeploymentEvent(alienDeployment.getDeploymentPaaSId(), alienDeployment.getDeploymentId(), DeploymentStatus.DEPLOYMENT_IN_PROGRESS);
        Path blueprintPath;
        try {
            blueprintPath = blueprintService.generateBlueprint(alienDeployment);
        } catch (IOException | CSARVersionNotFoundException e) {
            log.error(
                    "Unable to generate the blueprint for " + alienDeployment.getDeploymentPaaSId() + " with alien deployment id "
                            + alienDeployment.getDeploymentId(), e);
            eventService.registerDeploymentEvent(alienDeployment.getDeploymentPaaSId(), alienDeployment.getDeploymentId(), DeploymentStatus.FAILURE);
            return Futures.immediateFailedFuture(e);
        }
        ListenableFuture<Blueprint> createdBlueprint = blueprintDAO.asyncCreate(alienDeployment.getDeploymentPaaSId(), blueprintPath.toString());
        AsyncFunction<Blueprint, Deployment> createDeploymentFunction = new AsyncFunction<Blueprint, Deployment>() {
            @Override
            public ListenableFuture<Deployment> apply(Blueprint blueprint) throws Exception {
                return waitForDeploymentExecutionsFinish(deploymentDAO.asyncCreate(alienDeployment.getDeploymentPaaSId(), blueprint.getId(),
                        Maps.<String, Object> newHashMap()));
            }
        };
        ListenableFuture<Deployment> createdDeployment = Futures.transform(createdBlueprint, createDeploymentFunction);
        AsyncFunction<Deployment, Execution> startExecutionFunction = new AsyncFunction<Deployment, Execution>() {
            @Override
            public ListenableFuture<Execution> apply(Deployment deployment) throws Exception {
                return waitForExecutionFinish(executionDAO.asyncStart(deployment.getId(), Workflow.INSTALL, null, false, false));
            }
        };
        ListenableFuture<Execution> executionFuture = Futures.transform(createdDeployment, startExecutionFunction);
        addFailureCallback(executionFuture, "Deployment", alienDeployment.getDeploymentPaaSId(), alienDeployment.getDeploymentId(), DeploymentStatus.FAILURE);
        return executionFuture;
    }

    public ListenableFuture<?> undeploy(final PaaSDeploymentContext deploymentContext) {
        log.info("Undeploying recipe {} with alien's deployment id {}", deploymentContext.getDeploymentPaaSId(), deploymentContext.getDeploymentId());
        eventService.registerDeploymentEvent(deploymentContext.getDeploymentPaaSId(), deploymentContext.getDeploymentId(),
                DeploymentStatus.UNDEPLOYMENT_IN_PROGRESS);
        try {
            FileUtil.delete(blueprintService.resolveBlueprintPath(deploymentContext.getDeploymentPaaSId()));
        } catch (IOException e) {
            log.warn("Unable to delete generated blueprint for recipe " + deploymentContext.getDeploymentPaaSId(), e);
        }
        ListenableFuture<?> startUninstall = waitForExecutionFinish(executionDAO.asyncStart(deploymentContext.getDeploymentPaaSId(), Workflow.UNINSTALL, null,
                false, true));
        AsyncFunction deleteDeploymentFunction = new AsyncFunction() {
            @Override
            public ListenableFuture<?> apply(Object input) throws Exception {
                // TODO Due to bug index not refreshed of cloudify 3.1 (will be corrected in 3.2). We schedule the delete of deployment 2 seconds after the
                // end of uninstall operation
                ListenableFuture<?> scheduledDeleteDeployment = Futures.dereference(scheduledExecutorService.schedule(new Callable<ListenableFuture<?>>() {
                    @Override
                    public ListenableFuture<?> call() throws Exception {
                        return deploymentDAO.asyncDelete(deploymentContext.getDeploymentPaaSId());
                    }
                }, 2, TimeUnit.SECONDS));
                return scheduledDeleteDeployment;
            }
        };
        ListenableFuture<?> deletedDeployment = Futures.transform(startUninstall, deleteDeploymentFunction);
        // TODO Due to bug index not refreshed of cloudify 3.1 (will be corrected in 3.2). We schedule the delete of blueprint 2 seconds after the delete of
        // deployment
        AsyncFunction deleteBlueprintFunction = new AsyncFunction() {
            @Override
            public ListenableFuture<?> apply(Object input) throws Exception {
                ListenableFuture<?> scheduledDeleteBlueprint = Futures.dereference(scheduledExecutorService.schedule(new Callable<ListenableFuture<?>>() {
                    @Override
                    public ListenableFuture<?> call() throws Exception {
                        return blueprintDAO.asyncDelete(deploymentContext.getDeploymentPaaSId());
                    }
                }, 2, TimeUnit.SECONDS));
                return scheduledDeleteBlueprint;
            }
        };
        ListenableFuture<?> undeploymentFuture = Futures.transform(deletedDeployment, deleteBlueprintFunction);
        addFailureCallback(undeploymentFuture, "Undeployment", deploymentContext.getDeploymentPaaSId(), deploymentContext.getDeploymentId(),
                DeploymentStatus.UNDEPLOYED);
        return undeploymentFuture;
    }

    private void addFailureCallback(ListenableFuture future, final String operationName, final String deploymentPaaSId, final String deploymentId,
            final DeploymentStatus status) {
        Futures.addCallback(future, new FutureCallback<Execution>() {
            @Override
            public void onSuccess(Execution result) {
                log.info(operationName + " of deployment {} with alien's deployment id {} has been executed asynchronously", deploymentPaaSId, deploymentId);
            }

            @Override
            public void onFailure(Throwable t) {
                log.error(operationName + " of deployment " + deploymentPaaSId + " with alien's deployment id " + deploymentId + " has failed", t);
                eventService.registerDeploymentEvent(deploymentPaaSId, deploymentId, status);
            }
        });
    }
}
