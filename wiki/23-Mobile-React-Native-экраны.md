Сессия 8. Mobile-клиент: экраны · 75–150 мин

# 1. Навигация (75–90 мин)

`src/mobile/src/navigation/RootNavigator.tsx`:

```tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '../auth/AuthContext';
import { LoginScreen } from '../screens/LoginScreen';
import { TasksScreen } from '../screens/TasksScreen';
import { TaskFormScreen } from '../screens/TaskFormScreen';

export type RootStackParamList = {
  Login: undefined;
  Tasks: undefined;
  TaskForm: { taskId?: number };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  const { user, isInitializing } = useAuth();

  if (isInitializing) {
    return null;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: true }}>
        {user ? (
          <>
            <Stack.Screen name="Tasks" component={TasksScreen} options={{ title: 'Задачи' }} />
            <Stack.Screen name="TaskForm" component={TaskFormScreen} options={{ title: 'Задача' }} />
          </>
        ) : (
          <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'Вход' }} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

`App.tsx`:

```tsx
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from './src/auth/AuthContext';
import { RootNavigator } from './src/navigation/RootNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar style="dark" />
        <RootNavigator />
      </AuthProvider>
    </SafeAreaProvider>
  );
}
```

> **Замечание:** стек строится по наличию пользователя. При выходе стек
> пересобирается и показывает только `Login` — «застревания» на закрытом
> экране не бывает. Отдельный guard не нужен.

# 2. Экран входа (90–105 мин)

`src/mobile/src/screens/LoginScreen.tsx`:

```tsx
import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useAuth } from '../auth/AuthContext';
import { ApiError } from '../api/client';

export function LoginScreen() {
  const { login, register } = useAuth();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function handleSubmit() {
    setError('');

    if (!email.trim() || !password) {
      setError('Заполните email и пароль');
      return;
    }

    if (mode === 'register' && !fullName.trim()) {
      setError('Укажите имя');
      return;
    }

    setBusy(true);

    try {
      if (mode === 'register') {
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Что-то пошло не так');
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Планировщик задач</Text>
        <Text style={styles.subtitle}>
          {mode === 'login' ? 'Войдите, чтобы увидеть свои задачи' : 'Создайте аккаунт'}
        </Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        {mode === 'register' && (
          <TextInput
            style={styles.input}
            placeholder="Имя и фамилия"
            value={fullName}
            onChangeText={setFullName}
            autoCapitalize="words"
          />
        )}

        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
        />

        <TextInput
          style={styles.input}
          placeholder="Пароль"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoCapitalize="none"
        />

        <TouchableOpacity
          style={[styles.button, busy && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={busy}
        >
          {busy ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.buttonText}>
              {mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
            </Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.link}
          onPress={() => {
            setMode(mode === 'login' ? 'register' : 'login');
            setError('');
          }}
        >
          <Text style={styles.linkText}>
            {mode === 'login' ? 'Нет аккаунта? Зарегистрируйтесь' : 'Уже есть аккаунт? Войдите'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#F1F6F2' },
  container: { padding: 24, paddingTop: 64 },
  title: { fontSize: 26, fontWeight: '700', color: '#364046' },
  subtitle: { marginTop: 6, marginBottom: 24, color: '#6D797F' },
  error: {
    backgroundColor: '#FDECEC',
    borderColor: '#D13C3C',
    borderWidth: 1,
    color: '#D13C3C',
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DDE3E0',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    marginBottom: 12,
  },
  button: {
    backgroundColor: '#0F9346',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  link: { marginTop: 20, alignItems: 'center' },
  linkText: { color: '#0F9346', fontSize: 14 },
});
```

> **Замечание:** `KeyboardAvoidingView` + `ScrollView` обязательны. Без них
> клавиатура на Android закрывает кнопку входа, и нажать её невозможно.

# 3. Экран списка (105–130 мин)

`src/mobile/src/screens/TasksScreen.tsx`:

```tsx
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import type { Task, TaskStatus } from '../api/types';
import { ApiError, tasksApi } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Tasks'>;

const STATUS_LABELS: Record<TaskStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  done: 'Выполнена',
  cancelled: 'Отменена',
};

const FILTERS: Array<{ value: TaskStatus | undefined; label: string }> = [
  { value: undefined, label: 'Все' },
  { value: 'new', label: 'Новые' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'done', label: 'Готово' },
];

function formatDate(value: string | null): string {
  if (!value) return 'Без срока';

  const date = new Date(value);

  return `${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}.${date.getFullYear()}`;
}

function isOverdue(task: Task): boolean {
  if (task.status === 'done' || !task.dueDate) return false;

  return task.dueDate < new Date().toISOString().slice(0, 10);
}

export function TasksScreen({ navigation }: Props) {
  const { logout } = useAuth();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [status, setStatus] = useState<TaskStatus | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const result = await tasksApi.list(status);

      setTasks(result.items);
      setError('');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Не удалось загрузить задачи');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [status]);

  // Загрузка при монтировании и при смене фильтра
  useState(() => {
    void load();
  });

  async function handleToggle(task: Task) {
    try {
      await tasksApi.toggleCompleted(task.id);
      await load();
    } catch (e) {
      Alert.alert('Ошибка', e instanceof ApiError ? e.message : 'Не удалось изменить задачу');
    }
  }

  function handleDelete(task: Task) {
    Alert.alert('Удалить задачу', `Удалить «${task.title}»?`, [
      { text: 'Отмена', style: 'cancel' },
      {
        text: 'Удалить',
        style: 'destructive',
        onPress: async () => {
          try {
            await tasksApi.remove(task.id);
            await load();
          } catch (e) {
            Alert.alert('Ошибка', e instanceof ApiError ? e.message : 'Не удалось удалить');
          }
        },
      },
    ]);
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0F9346" />
      </View>
    );
  }

  return (
    <View style={styles.flex}>
      <View style={styles.toolbar}>
        <TouchableOpacity style={styles.addButton} onPress={() => navigation.navigate('TaskForm', {})}>
          <Text style={styles.addButtonText}>+ Новая задача</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={logout}>
          <Text style={styles.logout}>Выйти</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.filters}>
        {FILTERS.map((filter) => (
          <TouchableOpacity
            key={filter.label}
            style={[styles.filterChip, status === filter.value && styles.filterChipActive]}
            onPress={() => {
              setStatus(filter.value);
              setLoading(true);
            }}
          >
            <Text style={[styles.filterText, status === filter.value && styles.filterTextActive]}>
              {filter.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <FlatList
        data={tasks}
        keyExtractor={(item) => String(item.id)}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(); }} />
        }
        ListEmptyComponent={
          <Text style={styles.empty}>Задач нет. Нажмите «Новая задача».</Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.card, isOverdue(item) && styles.cardOverdue]}
            onPress={() => navigation.navigate('TaskForm', { taskId: item.id })}
            onLongPress={() => handleDelete(item)}
          >
            <View style={styles.cardHead}>
              <TouchableOpacity
                onPress={() => handleToggle(item)}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <View style={[styles.checkbox, item.status === 'done' && styles.checkboxDone]}>
                  {item.status === 'done' && <Text style={styles.checkmark}>✓</Text>}
                </View>
              </TouchableOpacity>

              <Text style={[styles.title, item.status === 'done' && styles.titleDone]}>
                {item.title}
              </Text>
            </View>

            <View style={styles.meta}>
              <Text style={styles.badge}>{STATUS_LABELS[item.status]}</Text>
              <Text style={styles.badge}>{item.priority}</Text>
              <Text style={styles.due}>
                {formatDate(item.dueDate)}
                {isOverdue(item) ? ' — просрочена' : ''}
              </Text>
            </View>

            <Text style={styles.hint}>долгое нажатие — удалить</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#F1F6F2' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  toolbar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  addButton: { backgroundColor: '#0F9346', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 10 },
  addButtonText: { color: '#FFFFFF', fontWeight: '700' },
  logout: { color: '#6D797F' },
  filters: { flexDirection: 'row', paddingHorizontal: 16, gap: 8, flexWrap: 'wrap' },
  filterChip: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DDE3E0',
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 6,
  },
  filterChipActive: { backgroundColor: '#0F9346', borderColor: '#0F9346' },
  filterText: { color: '#364046', fontSize: 13 },
  filterTextActive: { color: '#FFFFFF' },
  error: { margin: 16, color: '#D13C3C' },
  empty: { textAlign: 'center', color: '#6D797F', marginTop: 48, paddingHorizontal: 24 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginHorizontal: 16,
    marginTop: 12,
    borderLeftWidth: 4,
    borderLeftColor: 'transparent',
  },
  cardOverdue: { borderLeftColor: '#D13C3C' },
  cardHead: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#0F9346',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxDone: { backgroundColor: '#0F9346' },
  checkmark: { color: '#FFFFFF', fontWeight: '700' },
  title: { flex: 1, fontSize: 16, fontWeight: '500', color: '#364046' },
  titleDone: { textDecorationLine: 'line-through', color: '#6D797F' },
  meta: { flexDirection: 'row', gap: 8, marginTop: 10, alignItems: 'center', flexWrap: 'wrap' },
  badge: {
    backgroundColor: '#F1F6F2',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 2,
    fontSize: 12,
    color: '#364046',
  },
  due: { fontSize: 12, color: '#6D797F' },
  hint: { marginTop: 8, fontSize: 11, color: '#BDC6CB' },
});
```

> **Замечание:** `useState(() => { void load(); })` — неправильный хук: его
> аргумент это значение, а не эффект, и загрузка не выполнится. Замените на
> честный `useEffect`:

```tsx
import { useEffect } from 'react';

useEffect(() => {
  setLoading(true);
  void load();
}, [load]);
```

# 4. Экран формы (130–140 мин)

`src/mobile/src/screens/TaskFormScreen.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import type { Task, TaskPriority, TaskStatus } from '../api/types';
import { ApiError, tasksApi } from '../api/client';

type Props = NativeStackScreenProps<RootStackParamList, 'TaskForm'>;

const STATUSES: TaskStatus[] = ['new', 'in_progress', 'done', 'cancelled'];
const PRIORITIES: TaskPriority[] = ['low', 'medium', 'high'];

const STATUS_LABELS: Record<TaskStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  done: 'Выполнена',
  cancelled: 'Отменена',
};

const PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
};

export function TaskFormScreen({ navigation, route }: Props) {
  const taskId = route.params?.taskId;

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('medium');
  const [status, setStatus] = useState<TaskStatus>('new');
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(taskId !== undefined);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (taskId === undefined) return;

    let cancelled = false;

    tasksApi
      .list()
      .then((result) => {
        if (cancelled) return;

        const task: Task | undefined = result.items.find((x) => x.id === taskId);

        if (!task) return;

        setTitle(task.title);
        setDescription(task.description ?? '');
        setPriority(task.priority);
        setStatus(task.status);
        setDueDate(task.dueDate ?? '');
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          Alert.alert('Ошибка', e instanceof ApiError ? e.message : 'Не удалось загрузить задачу');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [taskId]);

  async function handleSave() {
    if (!title.trim()) {
      Alert.alert('Ошибка', 'Название обязательно');
      return;
    }

    setBusy(true);

    const payload = {
      title: title.trim(),
      description: description.trim() === '' ? null : description.trim(),
      priority,
      status,
      dueDate: dueDate === '' ? null : dueDate,
    };

    try {
      if (taskId === undefined) {
        await tasksApi.create(payload);
      } else {
        await tasksApi.update(taskId, payload);
      }

      navigation.goBack();
    } catch (e) {
      Alert.alert('Ошибка', e instanceof ApiError ? e.message : 'Не удалось сохранить');
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (taskId === undefined) return;

    try {
      await tasksApi.remove(taskId);
      navigation.goBack();
    } catch (e) {
      Alert.alert('Ошибка', e instanceof ApiError ? e.message : 'Не удалось удалить');
    }
  }

  if (loading) {
    return <View style={styles.flex} />;
  }

  return (
    <ScrollView style={styles.flex} contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <TextInput style={styles.input} placeholder="Название *" value={title} onChangeText={setTitle} />
      <TextInput
        style={[styles.input, styles.multiline]}
        placeholder="Описание"
        value={description}
        onChangeText={setDescription}
        multiline
        numberOfLines={4}
      />

      <Text style={styles.label}>Срок (ГГГГ-ММ-ДД)</Text>
      <TextInput
        style={styles.input}
        placeholder="2026-10-15"
        value={dueDate}
        onChangeText={setDueDate}
        autoCapitalize="none"
      />

      <Text style={styles.label}>Приоритет</Text>
      <View style={styles.chips}>
        {PRIORITIES.map((value) => (
          <TouchableOpacity
            key={value}
            style={[styles.chip, priority === value && styles.chipActive]}
            onPress={() => setPriority(value)}
          >
            <Text style={[styles.chipText, priority === value && styles.chipTextActive]}>
              {PRIORITY_LABELS[value]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Статус</Text>
      <View style={styles.chips}>
        {STATUSES.map((value) => (
          <TouchableOpacity
            key={value}
            style={[styles.chip, status === value && styles.chipActive]}
            onPress={() => setStatus(value)}
          >
            <Text style={[styles.chipText, status === value && styles.chipTextActive]}>
              {STATUS_LABELS[value]}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <TouchableOpacity style={[styles.button, busy && styles.buttonDisabled]} onPress={handleSave} disabled={busy}>
        <Text style={styles.buttonText}>{busy ? 'Сохраняем…' : 'Сохранить'}</Text>
      </TouchableOpacity>

      {taskId !== undefined && (
        <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
          <Text style={styles.deleteText}>Удалить задачу</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#F1F6F2' },
  container: { padding: 16, paddingBottom: 48 },
  label: { marginTop: 12, marginBottom: 8, color: '#6D797F', fontSize: 14 },
  input: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DDE3E0',
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    marginBottom: 12,
  },
  multiline: { minHeight: 96, textAlignVertical: 'top' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  chip: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DDE3E0',
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  chipActive: { backgroundColor: '#0F9346', borderColor: '#0F9346' },
  chipText: { color: '#364046' },
  chipTextActive: { color: '#FFFFFF' },
  button: {
    backgroundColor: '#0F9346',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  deleteButton: { marginTop: 12, padding: 16, alignItems: 'center' },
  deleteText: { color: '#D13C3C', fontSize: 16 },
});
```

# 5. Скриншоты для сдачи (140–150 мин)

Скриншоты обязательны по заданию. Снимайте **на устройстве или эмуляторе**,
не в браузере.

```bash
mkdir -p docs/screenshots
```

Снимите 5–6 экранов:

| Файл | Что на нём |
|---|---|
| `mobile-login.png` | экран входа |
| `mobile-tasks.png` | список задач |
| `mobile-task-form.png` | форма создания/редактирования |
| `mobile-task-done.png` | задача отмечена выполненной |
| `mobile-filters.png` | список с фильтром |

Способ для Android-эмулятора:

```bash
adb exec-out screencap -p > docs/screenshots/mobile-tasks.png
```

Для физического телефона — кнопки питания + громкости, затем перенесите файл
в репозиторий.

Добавьте скриншоты в README раздела «Mobile-клиент».

# Проверка

1. `npx expo start` → приложение работает на устройстве или эмуляторе.
2. Вход и регистрация работают, ошибки показываются в `Alert`.
3. Список загружается при старте, кнопка фильтра перезапрашивает данные,
   «потянуть вниз» обновляет.
4. Галочка отмечает задачу выполненной — состояние обновляется после ответа API.
5. Нажатие на карточку открывает форму с заполненными полями.
6. Создание новой задачи возвращает на список, задача есть.
7. Удаление — по долгому нажатию, с подтверждением.
8. Закрытие и запуск приложения → пользователь остаётся внутри (токен в
   `SecureStore`).
9. Скриншоты сняты и лежат в `docs/screenshots/`.

```bash
# токен не должен попасть в бандл читаемым файлом
grep -r "eyJhbGciOi" src/mobile/ 2>/dev/null
# пусто
```

# Коммит

```bash
git add src/mobile docs/screenshots
git commit -m "Mobile-клиент: навигация, экраны входа/списка/формы, скриншоты"
```

# Если что-то не получилось

| Симптом | Что делать |
|---|---|
| `useState` вместо `useEffect` для загрузки | исправьте хук, иначе данные не загрузятся |
| Клавиатура закрывает кнопку | оберните в `KeyboardAvoidingView` + `ScrollView` |
| `Alert.alert` не появляется | проверьте `enabled` у кнопки |
| Задача не обновляется после переключения | после мутации вызывайте `load()` заново |
| Скриншот через `adb` пустой | эмулятор должен быть запущен; `adb devices` покажет состояние |
| `secure-store` не работает на web | проверяйте на устройстве; в web используйте `localStorage` |

# Итог сессии 8

Раздел «Mobile-клиент — 15 баллов»:

- [x] React Native, приложение запускается на устройстве или эмуляторе
- [x] 3 экрана: вход, список, создание/редактирование
- [x] авторизация, токен сохраняется между запусками (`SecureStore`)
- [x] создание, изменение, отметка выполнения, удаление
- [x] скриншоты приложения в репозитории

## Иллюстрации

![[images/mob23-list.png]]
*Список задач: сводка, поиск, фильтры-чипы, карточки*

![[images/mob23-filter.png]]
*Фильтр-чип меняет запрос к API*

![[images/mob23-create.png]]
*Создание задачи на телефоне*

![[images/mob23-created.png]]
*Задача появилась в списке, сводка пересчитана*

![[images/mob23-done.png]]
*Выполненная задача зачёркнута*

![[gifs/mobile-scenario.gif]]
*Мобильный сценарий: вход, фильтр, создание, выполнение, удаление*

---

Дальше: [24-Документирование-README-и-Postman](24-Документирование-README-и-Postman)
