// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.13;

import {Script, console2} from "forge-std/Script.sol";
import {BetterDeployer} from "better-deployer/BetterDeployer.sol";

contract Deploy is BetterDeployer {
    function strCmp(string memory a, string memory b) private returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function run() public {
        // Setup wallet
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        string memory filename = vm.envString("filename");
        string memory contractName = vm.envString("contract");
        vm.startBroadcast(deployerPrivateKey);

        // skip file generation
        setSkipFile(true);

        // Log address
        address deployerAddress = vm.addr(deployerPrivateKey);
        console2.log("Loaded deployer: ", deployerAddress);

        address coordinator = 0x5FbDB2315678afecb367f032d93F642f64180aa3;

        string memory artifact = string.concat("./out/", filename, "/", contractName, ".json");
        address consumer = deploy("consumer", artifact, abi.encode(coordinator));

        console2.log("Deployed Contract: ", address(consumer));

        // Execute
        vm.stopBroadcast();
        vm.broadcast();
    }
}
