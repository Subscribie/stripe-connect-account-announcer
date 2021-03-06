import { serve } from "https://deno.land/std@0.80.0/http/server.ts";
import { config } from "https://deno.land/x/dotenv@v1.0.1/mod.ts";


// Load config from .env
console.log(config({ export: true}));

const DENO_PORT = parseInt(Deno.env.get('DENO_PORT'));
const HOSTNAME = Deno.env.get('HOSTNAME');
const BIND_ADDRESS = Deno.env.get('BIND_ADDRESS');
const REDIS_HOSTNAME = Deno.env.get('REDIS_HOSTNAME');
const REDIS_PORT = parseInt(Deno.env.get('REDIS_PORT'));
const REDIS_PASSWORD = Deno.env.get('REDIS_PASSWORD');

const s = serve({ hostname: BIND_ADDRESS, port: DENO_PORT});
console.log("BIND_ADDRESS:" + BIND_ADDRESS);
console.log("http://:" + HOSTNAME + ":" + DENO_PORT);

const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8');

const redisConn = await Deno.connect({hostname: REDIS_HOSTNAME, port: REDIS_PORT})
// Login to redis
redisConn.write(encoder.encode(`AUTH ${REDIS_PASSWORD}\n\n`));
const loginBuf = new Uint8Array(1024);
await redisConn.read(loginBuf);
console.log(decoder.decode(loginBuf));


for await (const req of s) {
  const requestBody = await decoder.decode(await Deno.readAll(req.body));
  const parsedBody = JSON.parse(requestBody);
  const stripe_connect_account_id = parsedBody['stripe_connect_account_id'];
  const site_url = parsedBody['site_url'];
  const live_mode = parsedBody['live_mode'];

  // Store the stripe_connect_account_id against the shop_url
  console.log([site_url, stripe_connect_account_id, live_mode]);
  // Send stripe connect account id and shop url as key/value
  redisConn.write(encoder.encode(`set ${stripe_connect_account_id} ${site_url}\n\n`));
  // Read response from redis
  const buf = new Uint8Array(1024);
  await redisConn.read(buf);
  console.log(decoder.decode(buf));

  const msg = `Stripe connect account added or updated. site_url: ${site_url} account: ${stripe_connect_account_id}.`;
  console.log(msg);
  req.respond({ body: msg});
}


