import { Module } from '@nestjs/common';
import { __NAME__Controller } from './__LOWERNAME__.controller';
import { __NAME__Service } from './__LOWERNAME__.service';

@Module({
  controllers: [__NAME__Controller],
  providers: [__NAME__Service],
  exports: [__NAME__Service],
})
export class __NAME__Module {}
