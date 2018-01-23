package com.mesosphere.sdk.activemq.scheduler;

import com.mesosphere.sdk.activemq.api.FileResources;
import com.mesosphere.sdk.curator.CuratorUtils;
import com.mesosphere.sdk.scheduler.*;
import com.mesosphere.sdk.specification.DefaultServiceSpec;
import com.mesosphere.sdk.specification.yaml.RawServiceSpec;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;

/**
 * Main entry point for the Scheduler.
 */
public class Main {
    private static final Logger LOGGER = LoggerFactory.getLogger(Main.class);
    private static final String ACTIVEMQ_ZK_ADDR_ENV = "ACTIVEMQ_ZOOKEEPER_ADDRESS";
    private static final String ACTIVEMQ_RLDB_ZK_ADDR_ENV = "ACTIVEMQ_RLDB_ZKADDR";
    private static final String ACTIVEMQ_RLDB_ZK_PATH_ENV = "ACTIVEMQ_RLDB_ZKPATH";

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one file argument, got: " + Arrays.toString(args));
        }

        // Read config from provided file, and assume any config activemqs are in the same directory as the file:
//        File yamlSpecFile = new File(args[0]);
//        SchedulerRunner
//                .fromRawServiceSpec(
//                        RawServiceSpec.newBuilder(yamlSpecFile).build(),
//                        SchedulerConfig.fromEnv(),
//                        yamlSpecFile.getParentFile())
//                .run();

        LOGGER.info("Starting activemq scheduler");
        // Read config from provided file, and assume any config etcds are in the same directory as the file:
        SchedulerRunner
                .fromSchedulerBuilder(createSchedulerBuilder(new File(args[0])))
                .run();
    }

    private static SchedulerBuilder createSchedulerBuilder(File yamlSpecFile) throws Exception {
        RawServiceSpec rawServiceSpec = RawServiceSpec.newBuilder(yamlSpecFile).build();
        SchedulerConfig schedulerConfig = SchedulerConfig.fromEnv();

        // Allow users to manually specify a ZK location for kafka itself. Otherwise default to our service ZK location:
        String zookeeperAddr = System.getenv(ACTIVEMQ_ZK_ADDR_ENV);
        if (StringUtils.isEmpty(zookeeperAddr)) {
            // "master.mesos:2181" + "/dcos-service-path__to__my__activemq":
            zookeeperAddr = SchedulerUtils.getZkHost(rawServiceSpec, schedulerConfig);
        }
        LOGGER.info("Running ActiveMQ with zookeeper path: {}",
                zookeeperAddr + CuratorUtils.getServiceRootPath(rawServiceSpec.getName()));

        SchedulerBuilder schedulerBuilder = DefaultScheduler.newBuilder(
                DefaultServiceSpec
                        .newGenerator(rawServiceSpec, schedulerConfig, yamlSpecFile.getParentFile())
                        .setAllPodsEnv(ACTIVEMQ_RLDB_ZK_ADDR_ENV,
                                zookeeperAddr)
                        .setAllPodsEnv(ACTIVEMQ_RLDB_ZK_PATH_ENV,
                                CuratorUtils.getServiceRootPath(rawServiceSpec.getName()))
                        .build(),
                schedulerConfig)
                .setPlansFrom(rawServiceSpec);

        return schedulerBuilder
                .setCustomResources(getResources());
    }

    private static Collection<Object> getResources() {
        final Collection<Object> apiResources = new ArrayList<>();
        apiResources.add(new FileResources());
        return apiResources;
    }
}
