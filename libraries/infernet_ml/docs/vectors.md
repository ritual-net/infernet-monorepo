# Vector Utilities in Ritual

Ritual provides powerful utilities for working with vectors and tensors in blockchain applications through the `RitualVector` class. This abstraction makes it easy to convert between different tensor formats and encode/decode vectors for on-chain use.

## Key Features

- Seamless conversion between NumPy arrays, PyTorch tensors, and on-chain representations
- Support for both IEEE754 and fixed-point arithmetic
- Wide range of supported data types (integers, floats, complex numbers)
- Efficient encoding and decoding for blockchain storage and computation

## Working with Different Tensor Formats

### Converting Between Formats

`RitualVector` makes it simple to convert between different tensor formats:

```python
import numpy as np
import torch
from ritual import RitualVector

# Create from NumPy array
numpy_array = np.array([1.0, 2.0, 3.0])
vector = RitualVector.from_numpy(numpy_array)

# Convert to PyTorch tensor
torch_tensor = vector.tensor

# Create from PyTorch tensor
vector_from_torch = RitualVector.from_tensor(torch_tensor)
```

### Supported Data Types

Ritual supports a wide range of data types, automatically handling conversions between different formats:

- Floating point: float16, float32, float64, float128, float256
- Integers: int8, int16, int32, int64
- Unsigned integers: uint8, uint16, uint32, uint64
- Complex numbers: complex64, complex128
- Boolean values

## On-chain Representation

One of Ritual's key features is its ability to represent vectors on-chain using either IEEE754 or fixed-point arithmetic.

### Fixed-point Arithmetic

Fixed-point representation is commonly used in blockchain applications, similar to how ERC20 tokens handle decimals. This is particularly useful when working with smart contracts:

```python
# Create a vector
vector = RitualVector.from_numpy(np.array([1.5, 2.7, 3.2]))

# Encode using fixed-point arithmetic (18 decimals by default)
encoded_fixed = vector.to_web3(arithmetic="fixed_point")

# Decode back from fixed-point representation
decoded_vector = RitualVector.from_web3(encoded_fixed)
```

### IEEE754 Arithmetic

For cases where IEEE754 floating-point precision is preferred:

```python
# Encode using IEEE754 arithmetic (default)
encoded_ieee = vector.to_web3(arithmetic="ieee")

# Decode from IEEE754 representation
decoded_vector = RitualVector.from_web3(encoded_ieee)
```

## Working with Smart Contracts

When interfacing with smart contracts, `RitualVector` handles the encoding and decoding of vector data automatically:

```python
# Example of preparing vector data for a smart contract
vector = RitualVector.from_numpy(model_weights)
encoded_weights = vector.to_web3(
    arithmetic="fixed_point",
    fixed_point_scale=18  # Match your contract's decimal precision
)

# The encoded weights can now be sent to your smart contract
contract.functions.updateWeights(encoded_weights).transact()

# When reading from the contract, decode the data
encoded_data = contract.functions.getWeights().call()
decoded_vector = RitualVector.from_web3(encoded_data)
weights = decoded_vector.numpy  # Convert back to NumPy array
```

## Best Practices

1. **Choose the Right Arithmetic**:
   - Use fixed-point arithmetic when working with smart contracts that expect decimal scaling
   - Use IEEE754 when precise floating-point representation is needed

2. **Match Decimal Precision**:
   - When using fixed-point arithmetic, make sure the `fixed_point_scale` matches your smart contract's decimal precision
   - Common values are 18 (default) or 6 decimals

3. **Data Type Considerations**:
   - Choose appropriate data types based on your precision needs and gas costs
   - Smaller data types (e.g., float16) use less gas but have lower precision
   - Larger data types (e.g., float256) provide more precision but cost more gas

4. **Memory Efficiency**:
   - Use the smallest data type that meets your precision requirements
   - Consider batching multiple vectors together when making contract calls to reduce gas costs
