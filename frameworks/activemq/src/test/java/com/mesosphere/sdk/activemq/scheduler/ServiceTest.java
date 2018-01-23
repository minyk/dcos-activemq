package com.mesosphere.sdk.activemq.scheduler;

import org.junit.Test;
import com.mesosphere.sdk.testing.ServiceTestRunner;

public class ServiceTest {

    @Test
    public void testSpec() throws Exception {
        // `CLUSTER_NAME` and `CUSTOM_YAML_BLOCK` are set in our Main.java.
        // `ZONE` is set during offer evaluation.
        // `elastic-version` and `support-diagnostics-version` would normally be provided via elastic's
        // build.sh/versions.sh.
        new ServiceTestRunner()
                .run();
    }
}
