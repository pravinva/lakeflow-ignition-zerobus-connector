package com.example.ignition.zerobus.web;

/**
 * Static holder used by servlet implementations (javax/jakarta) to access the shared resource.
 *
 * This indirection avoids hard dependencies on a specific servlet API package (javax vs jakarta)
 * in the module startup code.
 */
public final class ZerobusConfigResourceHolder {
    private static volatile ZerobusConfigResource resource;

    private ZerobusConfigResourceHolder() {}

    public static void set(ZerobusConfigResource res) {
        resource = res;
    }

    public static ZerobusConfigResource get() {
        return resource;
    }
}


