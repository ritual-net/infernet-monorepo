# REST Client

We recommend interacting with the node's REST API via the [Infernet Client](https://github.com/ritual-net/infernet-monorepo-internal/tree/main/projects/infernet_client)
Python library or CLI.

## Health

Check the server's health. See [HealthInfo](./api#healthinfo).

=== "Python"

    ``` c
    #include <stdio.h>

    int main(void) {
      printf("Hello world!\n");
      return 0;
    }
    ```

=== "CLI"

    ``` c++
    #include <iostream>

    int main(void) {
      std::cout << "Hello world!" << std::endl;
      return 0;
    }
    ```

=== "cURL"
