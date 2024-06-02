// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {Script, console2} from "forge-std/Script.sol";
import {BetterDeployer} from "better-deployer/BetterDeployer.sol";

contract Deploy is BetterDeployer {
    function preRun() internal {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployerAddress = vm.addr(deployerPrivateKey);
        vm.startBroadcast(deployerPrivateKey);
        console2.log("Loaded deployer: ", deployerAddress);
        setPathAndFile("deployments", "deployments.json");
    }

    function postRun() internal {
        dump();
        vm.stopBroadcast();
        vm.broadcast();
    }

    function _deploy(string memory filename, string memory contractName) internal {
        address registry = vm.envAddress("registry");
        console2.log("Registry: ", registry);
        address signer = vm.envAddress("signer");
        string memory artifact = string.concat("./out/", filename, "/", contractName, ".json");
        address consumer;
        if (signer != address(0)) {
            console2.log("Signer: ", signer);
            consumer = deploy(contractName, artifact, abi.encode(registry, signer));
        } else {
            consumer = deploy(contractName, artifact, abi.encode(registry));
        }

        console2.log("Deployed Contract: ", address(consumer));
    }

    function run() public virtual {
        preRun();

        string memory filename = vm.envString("filename");
        string memory contractName = vm.envString("contract");
        _deploy(filename, contractName);

        postRun();
    }
}

contract DeployEverything is Deploy {
    function run() public override {
        preRun();

        _deploy("GenericCallbackConsumer.sol", "GenericCallbackConsumer");
        _deploy("InfernetErrors.sol", "InfernetErrors");
        _deploy("GenericSubscriptionConsumer.sol", "GenericSubscriptionConsumer");
        _deploy("FailingSubscriptionConsumer.sol", "FailingSubscriptionConsumer");
        _deploy("DelegateSubscriptionConsumer.sol", "DelegateSubscriptionConsumer");
        _deploy("FakeMoney.sol", "AcceptedMoney");
        _deploy("FakeMoney.sol", "RejectedMoney");
        postRun();
    }
}
