//https://github.com/status-im/status-network-token/blob/master/test/helpers/assertFail.js
module.exports = async function(callback) {
    let web3_error_thrown = false;
    try {
        const tr = await callback();
        if (tr && tr.receipt) {
          web3_error_thrown =
            (tr.receipt.status === '0x0') // geth
            || (tr.receipt.status === null); // parity
        }
    } catch (error) {
        if (error.message.search("invalid opcode")) web3_error_thrown = true;
    }
    assert.ok(web3_error_thrown, "Transaction should fail");
};
