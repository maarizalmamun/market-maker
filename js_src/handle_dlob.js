import { AnchorProvider } from '@coral-xyz/anchor';
import { Connection, Keypair, PublicKey } from '@solana/web3.js';
import {
	DriftClient,
	initialize,
	BulkAccountLoader,
	getMarketsAndOraclesForSubscription,
	DLOB,
	UserMap,
	Wallet,
	BN,
	convertToNumber,
	BASE_PRECISION,
	QUOTE_PRECISION,
	PRICE_PRECISION
} from "@drift-labs/sdk";
import dotenv from 'dotenv';
import fs from 'fs';
import bs58 from 'bs58';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
const env = 'devnet';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Construct the absolute path to the .env file
const pathToEnv = join(__dirname, '..', '.env');


// Load the environment variables
dotenv.config({ path: pathToEnv });
/* 
This code uses the template from sdk/src/examples/loadDlob.ts
And modifies it to read, filter, and store data from
dlob.getDLOBOrders()
*/
const main = async () => {
	// Initialize Drift SDK
	console.log(__dirname)
	const sdkConfig = initialize({ env });
	
    // Load privatekey
	const keypath = process.env.ANCHOR_WALLET;
    const privateKey = await get_privateKey(keypath);

	// Determine type(privatekey): base58 (string) or base64 (object)
	let keypair;
	if(typeof privateKey === "string"){
		//decode to Uint8Array object 
		const privateKeyBytes = bs58.decode(privateKey)
		keypair = Keypair.fromSecretKey(privateKeyBytes);
	}
	else { keypair = Keypair.fromSecretKey(Uint8Array.from((privateKey))); 
	}
    // Set up the Wallet, Provider, Connection
    const wallet = new Wallet(keypair);
	const rpcAddress = process.env.RPC_ADDRESS; // can use: https://api.devnet.solana.com for devnet; https://api.mainnet-beta.solana.com for mainnet;
	const connection = new Connection(rpcAddress);

	// Set up the Provider
	const provider = new AnchorProvider(connection, wallet,AnchorProvider.defaultOptions());

	// Set up the Drift Clearing House
	const driftPublicKey = new PublicKey(sdkConfig.DRIFT_PROGRAM_ID);
	const bulkAccountLoader = new BulkAccountLoader(connection,'confirmed',1000);
	const driftClient = new DriftClient({
		connection,
		wallet: provider.wallet,
		programID: driftPublicKey,
		...getMarketsAndOraclesForSubscription(env),
		accountSubscription: {
			type: 'polling',
			accountLoader: bulkAccountLoader,
		},
	});

	//console.log('Subscribing drift client...');
	await driftClient.subscribe();

	//console.log('Loading user map...');
	const userMap = new UserMap(driftClient, {
		type: 'polling',
		accountLoader: bulkAccountLoader,
	});

	// Fetches all users and subscribes for updates
	await userMap.subscribe();

	//console.log('Loading dlob from user map...');
	const dlob = new DLOB();
	await dlob.initFromUserMap(userMap, bulkAccountLoader.mostRecentSlot);

	const dlobOrders = dlob.getDLOBOrders()
	//console.log('number of orders', dlobOrders.length);

	// Search and store only SOL-PERP orders
	const SOLPERPOrders = dlobOrders.filter(order => {
		return order.order.marketIndex === 0 &&
			   JSON.stringify(order.order.marketType) === '{"perp":{}}';
	});

	let oracledata = driftClient.getOracleDataForPerpMarket(0)

	// Recreate JSON with data extracted and type adjustments
	const ourDLOB = SOLPERPOrders.map(order => {
	    return {
            user: order.user,
            orderType: Object.keys(order.order.orderType)[0],
            price: convertToNumber(order.order.price,PRICE_PRECISION),
			oracle_price: convertToNumber(oracledata.price,PRICE_PRECISION),
			oracle_twap: convertToNumber(oracledata.twap,PRICE_PRECISION),
			baseAssetAmount: convertToNumber(order.order.baseAssetAmount,BASE_PRECISION),
            baseAssetAmountFilled: convertToNumber(order.order.baseAssetAmountFilled,BASE_PRECISION),
            direction: Object.keys(order.order.direction)[0],
            existingPositionDirection: Object.keys(order.order.existingPositionDirection)[0],
            postOnly: order.order.postOnly.toString(),
            oraclePriceOffset: parseFloat(order.order.oraclePriceOffset)/PRICE_PRECISION
	    };
	});
	dlob.clear();

	// Create JSON for orders from User Account
	let userAddress = (await driftClient.getUserAccountPublicKey()).toBase58();
	const userOrders = dlobOrders.filter(order => {
		return String(order.order.user) === userAddress;
	});
	// Store DLOB in data directory
	const data = JSON.stringify(ourDLOB);
	const userOrderData = JSON.stringify(userOrders)
	const pathToDataDir = join(__dirname, '..','data/');
    const filename = join(__dirname, '..','data/','dlob.json');
    const filename2 = join(__dirname, '..','data/','userorders.json');
	create_JSON(filename, data);
	create_JSON(filename2,userOrderData);
	//console.log('Unsubscribing users...');
	await userMap.unsubscribe();

	//console.log('Unsubscribing drift client...');
	await driftClient.unsubscribe();
};

function get_privateKey(keypath) {
	return new Promise((resolve, reject) => {
	  fs.readFile(keypath, 'utf8', (err, data) => {
		if (err) {
		  reject(err);
		} else {
		  const parsedData = JSON.parse(data);
		  resolve(parsedData['secretKey']);
		}
	  });
	});
};

function create_JSON(filename, data) {
	fs.writeFile(filename, data, (err) => {
		if (err) {
			console.error(err);
		} else {
			console.log(`Data written to ${filename}`);
		}
	});
};

main();

