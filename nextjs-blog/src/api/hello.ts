import type { NextApiRequest,NextApiResponse } from "next";
import { mock, Random } from 'mockjs';


export default function handler(req: NextApiRequest, res: NextApiResponse) {
    res.status(200).json(mock({
        'list|10': [{
           'id|+1': 1,
           name: Random.cname(),
           age: Random.integer(18, 60),
           sex: Random.pick(['男', '女']),
           address: Random.county(true),
           birthday: Random.date("yyyy-MM-dd")
        }]
    }))
}