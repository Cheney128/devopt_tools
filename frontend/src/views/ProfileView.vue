<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Phone } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/authStore'
import { userApi } from '../api/auth'

const authStore = useAuthStore()
const activeTab = ref('profile')

// 个人信息表单
const profileFormRef = ref(null)
const profileForm = reactive({
  nickname: '',
  email: '',
  phone: ''
})

const profileRules = {
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

// 密码修改表单
const passwordFormRef = ref(null)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 加载用户信息
const loadUserInfo = () => {
  if (authStore.user) {
    profileForm.nickname = authStore.user.nickname || ''
    profileForm.email = authStore.user.email || ''
    profileForm.phone = authStore.user.phone || ''
  }
}

// 保存个人信息
const handleSaveProfile = async () => {
  const valid = await profileFormRef.value.validate().catch(() => false)
  if (!valid) return

  try {
    const response = await userApi.updateMyProfile({
      nickname: profileForm.nickname,
      email: profileForm.email,
      phone: profileForm.phone
    })

    // 更新 store 中的用户信息
    authStore.updateUserInfo(response)

    ElMessage.success('个人信息保存成功')
  } catch (error) {
    console.error('保存个人信息失败:', error)
  }
}

// 修改密码
const handleChangePassword = async () => {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  try {
    await userApi.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })

    ElMessage.success('密码修改成功，请重新登录')

    // 清空表单
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''

    // 延迟登出
    setTimeout(async () => {
      await authStore.logout()
      window.location.href = '/login'
    }, 1500)
  } catch (error) {
    console.error('修改密码失败:', error)
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<template>
  <div class="profile-view">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人中心</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="profile">
          <div class="profile-info">
            <div class="user-avatar-section">
              <el-avatar :size="80" :icon="User" />
              <div class="user-basic-info">
                <h3>{{ authStore.nickname }}</h3>
                <p class="username">@{{ authStore.username }}</p>
                <el-tag :type="authStore.isAdmin ? 'danger' : 'success'" size="small">
                  {{ authStore.isAdmin ? '管理员' : '普通用户' }}
                </el-tag>
              </div>
            </div>

            <el-divider />

            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              label-width="100px"
              class="profile-form"
            >
              <el-form-item label="用户名">
                <el-input v-model="authStore.username" disabled />
              </el-form-item>

              <el-form-item label="昵称">
                <el-input
                  v-model="profileForm.nickname"
                  placeholder="请输入昵称"
                  maxlength="50"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="profileForm.email"
                  placeholder="请输入邮箱"
                  :prefix-icon="Message"
                />
              </el-form-item>

              <el-form-item label="手机号">
                <el-input
                  v-model="profileForm.phone"
                  placeholder="请输入手机号"
                  :prefix-icon="Phone"
                  maxlength="20"
                />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="handleSaveProfile">
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <div class="password-section">
            <el-alert
              title="密码安全提示"
              description="建议定期更换密码，使用包含字母、数字和特殊字符的复杂密码"
              type="info"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />

            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="100px"
              class="password-form"
            >
              <el-form-item label="旧密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  placeholder="请输入旧密码"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="请输入新密码（6-20个字符）"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  :prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="handleChangePassword">
                  修改密码
                </el-button>
                <el-button @click="passwordFormRef.resetFields()">
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.profile-view {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  min-height: 500px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.profile-info {
  padding: 20px 0;
}

.user-avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.user-basic-info h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.username {
  margin: 0 0 8px 0;
  color: #909399;
  font-size: 14px;
}

.profile-form,
.password-form {
  max-width: 500px;
}

.password-section {
  padding: 20px 0;
}
</style>
