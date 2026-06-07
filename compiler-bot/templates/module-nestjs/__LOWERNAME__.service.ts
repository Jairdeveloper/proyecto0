import { Injectable } from '@nestjs/common';

@Injectable()
export class __NAME__Service {
  private items: any[] = [];

  create(data: any) {
    this.items.push(data);
    return { id: this.items.length, ...data };
  }

  findAll() {
    return this.items;
  }

  findOne(id: string) {
    return this.items[Number(id)];
  }

  update(id: string, data: any) {
    this.items[Number(id)] = { ...this.items[Number(id)], ...data };
    return this.items[Number(id)];
  }

  remove(id: string) {
    const item = this.items[Number(id)];
    this.items.splice(Number(id), 1);
    return item;
  }
}
