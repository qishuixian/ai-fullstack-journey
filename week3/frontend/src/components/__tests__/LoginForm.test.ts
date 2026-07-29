import { mount } from '@vue/test-utils'
import LoginForm from './../LoginForm.vue'
import { describe, it, expect } from 'vitest'

describe('LoginForm', () => {
  it('renders correctly', () => {
    const wrapper = mount(LoginForm)
    // 注意：emojis 在测试文件中可能显示为乱码，直接用字符串比较
    expect(wrapper.find('h1').text()).toBe('🤖 AI 助手')
    expect(wrapper.find('.auth-submit').text()).toBe('登录')
  })

  it('switches between login and register mode', async () => {
    const wrapper = mount(LoginForm)
    await wrapper.findAll('.tab-btn')[1].trigger('click')
    expect(wrapper.find('.auth-submit').text()).toBe('注册')
  })
})