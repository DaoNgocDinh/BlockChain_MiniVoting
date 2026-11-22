import assert from 'node:assert/strict';
import { createHash, createPublicKey, verify } from 'node:crypto';
import { readFileSync } from 'node:fs';

const fixture = JSON.parse(readFileSync(new URL('../docs/fixtures/wire-v1.json', import.meta.url), 'utf8'));
const {
  genesis_record: { genesis, genesis_hash: genesisHash },
  transaction,
  post_state: postState,
  prepare_votes: prepareVotes,
  prepared_certificate: preparedCertificate,
  commit_votes: commitVotes,
  finalized_block: { proposal, certificate },
  expected,
} = fixture;

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (typeof value === 'object' && value !== null) {
    const fields = Object.keys(value).sort().map((key) => {
      return `${JSON.stringify(key)}:${canonicalJson(value[key])}`;
    });
    return `{${fields.join(',')}}`;
  }
  return JSON.stringify(value);
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function signingBytes(domain, fields) {
  return Buffer.from(`MINIVOTING-V1/${domain}\0${canonicalJson(fields)}`, 'utf8');
}

function validSignature(domain, fields, publicHex, signature) {
  if (!/^[0-9a-f]{64}$/.test(publicHex) || !/^[0-9a-f]{128}$/.test(signature)) return false;
  const publicKey = createPublicKey({
    format: 'jwk',
    key: { kty: 'OKP', crv: 'Ed25519', x: Buffer.from(publicHex, 'hex').toString('base64url') },
  });
  return verify(null, signingBytes(domain, fields), publicKey, Buffer.from(signature, 'hex'));
}

function checkVector(fields, domain, bytesHex, publicKey, signature) {
  assert.equal(signingBytes(domain, fields).toString('hex'), bytesHex, `${domain} signing bytes`);
  assert.ok(validSignature(domain, fields, publicKey, signature), `${domain} signature`);
}

assert.equal(fixture.fixture_version, 1);
assert.equal(sha256(canonicalJson(genesis)), genesisHash);
const validators = new Map(genesis.validators.map(({ node_id, public_key }) => [node_id, public_key]));
assert.deepEqual([...validators.keys()], ['node1', 'node2', 'node3', 'node4']);
assert.equal(new Set(validators.values()).size, 4);
assert.equal(genesis.quorum, 3);

const { signature: txSignature, tx_id: txId, ...txFields } = transaction;
assert.equal(canonicalJson(txFields), expected.txn_unsigned_canonical_utf8);
const reorderedTx = Object.fromEntries(Object.entries(txFields).reverse());
assert.equal(canonicalJson(reorderedTx), expected.txn_unsigned_canonical_utf8);
assert.equal(sha256(canonicalJson(txFields)), txId);
assert.equal(sha256(Buffer.from(txFields.sender_public_key, 'hex')), txFields.sender);
checkVector(txFields, 'TX', expected.tx_signing_bytes_hex, txFields.sender_public_key, txSignature);
assert.ok(!validSignature('TX', { ...txFields, amount: txFields.amount + 1 }, txFields.sender_public_key, txSignature));

const { block, signature: proposalSignature, ...proposalFields } = proposal;
assert.deepEqual(block.transactions, [transaction]);
assert.equal(block.header.prev_hash, genesisHash);
assert.equal(canonicalJson(block.header), expected.block_header_canonical_utf8);
assert.equal(sha256(canonicalJson(block.header)), block.block_hash);
assert.equal(sha256(canonicalJson(block.transactions)), block.header.tx_list_hash);
assert.ok(Buffer.byteLength(canonicalJson(block), 'utf8') <= genesis.max_block_bytes);

const accounts = new Map(genesis.accounts.map((account) => [account.address, { ...account }]));
const sender = accounts.get(txFields.sender);
assert.ok(sender.balance >= txFields.amount);
assert.equal(sender.nonce + 1, txFields.nonce);
sender.balance -= txFields.amount;
sender.nonce = txFields.nonce;
const recipient = accounts.get(txFields.recipient) ?? { address: txFields.recipient, balance: 0, nonce: 0 };
recipient.balance += txFields.amount;
accounts.set(recipient.address, recipient);
const updated = [...accounts.keys()].sort().map((key) => accounts.get(key));
assert.deepEqual(updated, postState);
assert.equal(canonicalJson(updated), expected.post_state_canonical_utf8);
assert.equal(sha256(canonicalJson(updated)), block.header.state_hash);

const sharedContext = {
  protocol_version: genesis.protocol_version,
  chain_id: genesis.chain_id,
  height: block.header.height,
  view: 0,
  block_hash: block.block_hash,
};
assert.deepEqual(proposalFields, { ...sharedContext, phase: 'PROPOSE', sender_id: genesis.leader_id });
checkVector(proposalFields, 'PROPOSE', expected.proposal_signing_bytes_hex, validators.get(genesis.leader_id), proposalSignature);

function checkCertificate(phase, subject, { signatures, ...certContext }) {
  assert.deepEqual(certContext, sharedContext);
  const signers = Object.entries(signatures);
  assert.ok(signers.length >= genesis.quorum && signers.length <= validators.size);
  assert.equal(subject.length, signers.length);
  for (const [senderId, signature] of signers) {
    const vote = { ...certContext, phase, sender_id: senderId };
    assert.deepEqual(subject.find(({ sender_id: id }) => id === senderId), { ...vote, signature });
    assert.ok(validSignature(phase, vote, validators.get(senderId), signature), `${phase} by ${senderId}`);
  }
}

checkCertificate('PREPARE', prepareVotes, preparedCertificate);
checkCertificate('COMMIT', commitVotes, certificate);

const cases = [
  [prepareVotes, expected.prepare_node2_signing_bytes_hex],
  [commitVotes, expected.commit_node2_signing_bytes_hex],
];
for (const [votes, bytesHex] of cases) {
  const { signature, ...fields } = votes.find(({ sender_id: id }) => id === 'node2');
  const publicKey = validators.get(fields.sender_id);
  checkVector(fields, fields.phase, bytesHex, publicKey, signature);
  const otherPhase = fields.phase === 'PREPARE' ? 'COMMIT' : 'PREPARE';
  assert.ok(!validSignature(otherPhase, fields, publicKey, signature));
  assert.ok(!validSignature(otherPhase, { ...fields, phase: otherPhase }, publicKey, signature));
  for (const [field, value] of Object.entries({
    chain_id: 'other-chain',
    height: fields.height + 1,
    view: 1,
    protocol_version: 2,
  })) {
    assert.ok(!validSignature(fields.phase, { ...fields, [field]: value }, publicKey, signature), field);
  }
}

console.log('MiniVoting wire v1: verified canonical bytes, hashes, signatures, certificates and state');
